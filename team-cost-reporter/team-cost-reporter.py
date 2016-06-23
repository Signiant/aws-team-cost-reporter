import imp,argparse
import os,sys
import json,yaml
import pprint

# Project modules
import plugin
import output

def readConfigFile(path):
    configMap = []

    try:
        config_file_handle = open(path)
        configMap = yaml.load(config_file_handle)
        config_file_handle.close()
    except:
        print "Error: Unable to open config file %s" % path

    return configMap

## mainFile
def main(argv):
    plugin_results = dict()

    parser = argparse.ArgumentParser(description='Report on AWS costs by team')
    parser.add_argument('-d','--debug', help='Enable debug output',action='store_true')
    parser.add_argument('-c','--config', help='Full path to a config file',required=True)
    parser.add_argument('-t','--team', help='Team name to generate the repot for',required=True)
    args = parser.parse_args()

    configMap = readConfigFile(args.config)

    if configMap:
        # Invoke each of the plugins and store the results
        for config_plugin in configMap['plugins']:
            plugin_name = config_plugin['name']
            print "Loading plugin %s" % plugin_name
            plugin_handle = plugin.loadPlugin(plugin_name)
            plugin_results[plugin_name] = plugin_handle.getTeamCost(configMap)

        if args.debug: pprint.pprint(plugin_results)

        # Output the results for the run of each plugin
        output.outputResults(plugin_results)

if __name__ == "__main__":
   main(sys.argv[1:])
