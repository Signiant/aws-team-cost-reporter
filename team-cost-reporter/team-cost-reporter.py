import argparse
import os
import sys
import yaml
# Project modules
import plugin
import output


def readConfigFile(path):
    configMap = []

    try:
        config_file_handle = open(path)
        configMap = yaml.full_load(config_file_handle)
        config_file_handle.close()
    except:
        print("Error: Unable to open config file %s or invalid yaml" % path)

    return configMap


def main(argv):
    plugin_results = dict()

    # Add our folder to the system path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
            print("Loading plugin %s" % plugin_name)

            # Load the plugin from the plugins folder
            plugin_handle = plugin.loadPlugin(plugin_name)

            # Store the plugin output in a dict
            plugin_results[plugin_name] = plugin_handle.getTeamCost(args.team,configMap,args.debug)

        # Output the results for the run of each plugin
        output.outputResults(args.team,configMap,plugin_results,args.debug)

if __name__ == "__main__":
   main(sys.argv[1:])
