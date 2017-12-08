#!/usr/bin/env python
#-*- coding:utf-8 -*-
import os
import cmd
import subprocess
from lib.core.data import kb
from lib.core.data import conf
from lib.core.data import paths
from lib.core.common import banner
from lib.core.settings import HTTP_DEFAULT_HEADER,VERSION
from lib.core import log
from lib.core.manager import *
from thirdparty.colorama import init,Fore
from thirdparty.cmd2.cmd2 import Cmd
from lib.core.option import initializeKb

def initializeExp():
    expNumber = 0
    folders = []
    if not os.path.isdir(paths.ZEROSCAN_PLUGINS_PATH):
        os.makedirs(paths.ZEROSCAN_PLUGINS_PATH)
    folders.append(paths.ZEROSCAN_PLUGINS_PATH)
    for folder in folders:
        files = os.listdir(folder)
        for file in files:
            if file.endswith(".py") and "__init__" not in file:
                expNumber += 1
                kb.unloadedList.update({expNumber: os.path.join(folder, file)})
    kb.expNumbers = expNumber


init()

class baseConsole(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        os.system("clear")
        banner()

        conf.url = None
        conf.urlFile = None

        conf.cookie = None
        #随机ua的实现
        #conf.randomAgent = False

        conf.threads = 1

        #是否需要html报告
        conf.report = None

        conf.timeout = 3
        conf.httpHeaders = HTTP_DEFAULT_HEADER

        self.prompt = "ZEROScan > "


    def do_help(self, line):
        """
        帮助
        :return:
        """
        commands = {
            "help": "Help menu",
            "version": "Show the framework version numbers",
            "list": "List all plugins",
            "search <keyword>": "Search plugin names and descriptions",
            "info <plugin>": "Display information about one plugin",
            "use <plugin>": "Select a plugin by name",
            "options": "Display options for current plugin",
            "set <option> <value>": "Set a variable to a value",
            "run": "Run current plugin",
            "update": "Update the framework",
            "exit": "Exit the console"
        }
        print "\nCore Commands\n=============\n"
        print "%-30s%s" % ("Command", "Description")
        print "%-30s%s" % ("-------", "-----------")
        for command in commands:
            print "%-30s%s" % (command, commands[command])

    def do_version(self, line):
        """
        版本信息
        :return:
        """
        print
        print "Version: %s" % VERSION
        print

    def do_list(self, line):
        """
        插件列表
        :return:
        """
        print "\Modules\n=======\n"
        print "%-40s%-40s%-40s%s" % ("expName","appName", "appVersion", "description")
        print "%-40s%-40s%-40s%s" % ("-------", "-------", "----------","-----------")
        for ListPlugin in ListPlugins():
            print "%-40s%-40s%-40s%s" % (ListPlugin["expName"],ListPlugin["appName"], \
                                        ListPlugin["appVersion"], ListPlugin["description"])
        print

    def do_search(self, keyword):
        """
        搜索插件
        :param keyword: string, 关键字
        :return:
        """
        if keyword:
            print "\nMatching Modules\n================\n"
            print "%-40s%-40s%-40s%s" % ("expName","appName", "appVersion", "description")
            print "%-40s%-40s%-40s%s" % ("-------", "-------", "----------","-----------")
            for ListPlugin in SearchPlugin(keyword):
                print "%-40s%-40s%-40s%s" % (ListPlugin["expName"],ListPlugin["appName"], \
                                        ListPlugin["appVersion"], ListPlugin["description"])
        else:
            log.error("search <keyword>")

    def do_info(self,plugin):
        """
        插件信息
        :param plugin: string, 插件名称
        :return: 插件信息
        """
        if not plugin:
            if kb.CurrentPlugin:
                plugin = kb.CurrentPlugin
            else:
                log.error("info <plugin>")
                return
        if InfoPlugin(plugin):
            Infomation = InfoPlugin(plugin)
            print "\n%s: %s" % ("appName", Infomation["appName"])
            print "%s: %s" % ("appVersion", Infomation["appVersion"])
            print "Author:\n\t%s\n" % Infomation["author"]
            print "Description:\n\t%s\n" % Infomation["description"]
            print "Reference:\n\t%s\n" % Infomation["references"]
        else:
            log.error("Invalid plugin: %s" % plugin)

    def complete_info(self, text, line, begidx, endidx):
        """
        tab 补全
        :return:
        """
        plugins = []
        for ListPlugin in ListPlugins():
            plugins.append(ListPlugin["expName"])
        if not text:
            completions = plugins
        else:
            completions = [p for p in plugins if p.startswith(text)]
        return completions

    def do_use(self, plugin):
        """
        加载插件
        :param plugin: string, 插件名称
        :return:
        """
        initializeKb()
        ClearConf()

        kb.CurrentPlugin = plugin
        zsp = PluginBase(package='zsplugins')
        plugin_zsp = zsp.make_plugin_source(searchpath=[paths.ZEROSCAN_PLUGINS_PATH])
        expNames = plugin_zsp.list_plugins()
        if kb.CurrentPlugin:
            if plugin in expNames:
                self.prompt = "ZEROScan exploit({color}{content}{color_reset}) > ".format(
                    color=Fore.RED, content=kb.CurrentPlugin, color_reset=Fore.RESET)
            else:
                log.error("plugin is not exist!")
        else:
            log.error("use <plugin>")

    def complete_use(self, text, line, begidx, endidx):
        """
        tab 补全
        :return:
        """
        plugins = []
        for ListPlugin in ListPlugins():
            plugins.append(ListPlugin["expName"])
        if not text:
            completions = plugins
        else:
            completions = [p for p in plugins if p.startswith(text)]
        return completions

    def do_options(self, line):
        """
        插件设置项
        :return:
        """
        if kb.CurrentPlugin:
            rn = ShowOptions()
            if isinstance(rn, str):
                log.error(rn)
            else:
                print "\n\t%-20s%-40s%-10s%s" % ("Name", "Current Setting",
                                                 "Required", "Description")
                print "\t%-20s%-40s%-10s%s" % ("----", "---------------",
                                               "--------", "-----------")
                for option in rn:
                    print "\t%-20s%-40s%-10s%s" % (option["Name"],
                                                   option["Current Setting"],
                                                   option["Required"],
                                                   option["Description"])
                print
        else:
            log.error("Select a plugin first.")

    def do_set(self, arg):
        """
        设置参数
        :param arg: string, 以空格分割 option, value
        :return:
        """
        if kb.CurrentPlugin:
            if len(arg.split()) == 2:
                option = arg.split()[0]
                value = arg.split()[1]
                rn = SetOption(option, value)
                if rn.startswith("Invalid option:"):
                    log.error(rn)
                else:
                    print rn
            else:
                log.error("set <option> <value>")
        else:
            log.error("Select a plugin first.")

    def complete_set(self, text, line, begidx, endidx):
        """
        tab 补全
        :return:
        """
        option = []
        text = text.lower()
        for i in ShowOptions():
            option.append(i["Name"])
        if not text:
            completions = option
        else:
            completions = [o for o in option if o.lower().startswith(text)]
        return completions

    def do_run(self, line):
        """
        执行插件
        :return:
        """
        if kb.CurrentPlugin:
            ExecPlugin()
        else:
            log.error("Select a plugin first.")

    def do_update(self, line):
        """
        更新
        :return:
        """
        log.warn("")
        log.warn("you can update the ZEROScan by git")

    def do_back(self, line):
        """
        返回主菜单
        :param line:
        :return:
        """
        ClearConf()
        initializeKb()
        self.current_plugin = ""
        self.prompt = "ZEROScan > "

    def default(self, line):
        """
        无法识别命令时
        :param line:
        :return:
        """
        try:
            log.process("exec: %s" % line)
            SubCmd = subprocess.Popen(line, shell=True, stdout=subprocess.PIPE)
            print
            print SubCmd.communicate()[0]
        except:
            log.error("Unknown command: %s" % line)

    def do_exit(self, line):
        """
        退出
        :return:
        """
        exit()

    def emptyline(self):
        """
        空行
        :return:
        """
        pass
