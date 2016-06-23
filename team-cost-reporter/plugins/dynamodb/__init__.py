import json

# Project modules
import cloudcheckr

def id():
    return "dynamodb"

def log (message):
    print id() + ": " + message

def getTeamCost(team,configMap,debug):
    team_cost = dict()
    data_url = ''
    data = ''

    log("getting team cost for %s" % team)

    # get the data url for the dynamodb plugin url
    for config_plugin in configMap['plugins']:
        if config_plugin['name'] == id():
            print "plugin found"
            data_url = config_plugin['data_url']

    if data_url:
        data = cloudcheckr.loadData(data_url,"DynamoDbDetails",debug)
        if data:
            if debug: log("%i tables returned" % len(data['DynamoDbDetails']))
