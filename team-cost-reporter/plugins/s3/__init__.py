import urllib2,json,imp
import pprint

# Project modules
import cloudcheckr

def id():
    return "s3"

def log (message):
    print id() + ": " + message

def getTeamCost(team_name,configMap,debug):
    team_cost = dict(individual=dict())
    data_url = ''
    data = ''
    tag_to_match = ''
    days_to_report = configMap['global']['days_to_report']

    log("getting team cost for team: %s for %i days" % (team_name,days_to_report))

    # get the data url for the plugin
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

            if debug: log("Looking in cloudcheckr report data for tag name %s" % tag_to_match)

            # look in the data from cloudcheckr for a tag value matching that we are looking for
            for tag in data['Groupings']:
                # Assume the memberID/email in the config file is lower case
                member_id = str(tag['Name'].split(tag_to_match)[1]).strip().lower()
                if debug: log("member_id in cloudcheckr data is %s" % member_id)
                if member_id in team_members:
                    if debug: log("team member found in cloudcheckr data: %s" % member_id)

                    # Now we can get their cost from the cloudcheckr data
                    totalCost = 0
                    for costitem in tag['Costs']:
                        totalCost = totalCost + costitem['Amount']

                    if debug: log("total cost for %s is %s" % (member_id,totalCost))

                    team_cost['individual'][member_id] = format(float(totalCost),'.2f')

    return team_cost
