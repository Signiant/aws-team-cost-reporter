import imp
import os

pluginFolder = "./plugins"
mainFile = "__init__"

def getAllPlugins():
    plugins = []
    possibleplugins = os.listdir(pluginFolder)
    for i in possibleplugins:
        location = os.path.join(pluginFolder, i)
        if not os.path.isdir(location) or not mainFile + ".py" in os.listdir(location):
            continue
        info = imp.find_module(mainFile, [location])
        plugins.append({"name": i, "info": info})
    return plugins

def loadPlugin(pluginName):
    return imp.load_source(pluginName, os.path.join(pluginFolder, pluginName, mainFile + ".py"))

def getConfigFilePath():
    configPath = ""

    if "CONFIG_FILE" in os.environ:
        configPath = os.environ["CONFIG_FILE"]
    else:
        configPath = "./config.yaml"

    return configPath

# process ec2
plugin = loadPlugin('ec2')
retval = plugin.id()

print str(retval)

plugin = loadPlugin('eb')
retval = plugin.id()

print str(retval)

print getConfigFilePath()
