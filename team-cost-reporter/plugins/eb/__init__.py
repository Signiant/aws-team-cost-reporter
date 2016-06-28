import urllib2,json,imp
import pprint

# Project modules
import cloudcheckr

def log (message):
    print id() + ": " + message

def id():
    return "eb"

def getTeamCost(team_name,configMap,debug):
    team_cost = dict(shared=dict())
    data_url = ''
    data = ''
    tag_to_match = ''
    days_to_report = configMap['global']['days_to_report']

    log("getting team cost for team: %s for %i days" % (team_name,days_to_report))

    # get the data url for the ec2 plugin url
    for config_plugin in configMap['plugins']:
        if config_plugin['name'] == id():
            if debug: log("plugin info found in config file")
            data_url = config_plugin['data_url']

    if data_url:
        # get the report data from cloudcheckr which is by tag
        data = cloudcheckr.loadData(data_url,days_to_report,"Groupings",debug)
        if data:
            if debug: log("%i tags returned" % len(data['Groupings']))

            # Find our team info in the config file
            for team in configMap['teams']:
                if team['name'] == team_name:
                    team_members = team['members']
                    tag_to_match = team[id()]['include_tag']
                    config_envs = team[id()]['envs']

            totalCost = 0
            for config_match_env in config_envs:
                log("looking for eb env %s in cloudcheckr data" % config_match_env)

                for cc_env in data['Groupings']:
                    cc_env_name = str(cc_env['Name'].split(tag_to_match)[1]).strip().lower()

                    if debug: log("eb env in cloudcheckr data is %s" % cc_env_name)

                    # See if we're dealing with a wildcard or exact match
                    match = False
                    if str(config_match_env).startswith("*") and str(config_match_env).endswith("*"):
                        contain_match = config_match_env.split("*")[1]
                        if debug: log("wildcard matching- contains %s" % contain_match)

                        if contain_match.lower() in cc_env_name.lower():
                            if debug: log("Contains match found")
                            match = True
                    elif str(config_match_env).endswith("*"):
                        prefix = config_match_env.split("*")[0]
                        if debug: log("wildcard matching - prefix %s" % prefix)

                        if cc_env_name.lower().startswith(prefix.lower()):
                            if debug: log("Wildcard prefix match found")
                            match = True
                    elif str(config_match_env).startswith("*"):
                        suffix = config_match_env.split("*")[1]
                        if debug: log("wildcard matching - suffix %s" % suffix)

                        if cc_env_name.lower().endswith(suffix.lower()):
                            if debug: log("Wildcard suffix match found")
                            match = True
                    elif config_match_env == cc_env_name:
                        if debug: log("Exact matching")
                        match = True

                    if match:
                        # Match found - add cost
                        if debug: log("*** Matching eb env found")
                        for costitem in cc_env['Costs']:
                            totalCost = totalCost + costitem['Amount']

                            if debug: log("total cost for %s is %s" % (cc_env_name,totalCost))

                        team_cost['shared'][cc_env_name] = format(float(totalCost),'.2f')

    return team_cost
