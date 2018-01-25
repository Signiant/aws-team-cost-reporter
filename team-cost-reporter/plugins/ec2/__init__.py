# Project modules
import aws_cost_collector
import cloudcheckr


def id():
    return "ec2"


def log (message):
    print id() + ": " + message


def getTeamCost(team_name,configMap,debug):
    team_cost = dict(individual=dict())
    days_to_report = configMap['global']['days_to_report']

    log("getting team cost for team: %s for %i days" % (team_name,days_to_report))

    data = None
    for config_plugin in configMap['plugins']:
        if config_plugin['name'] == id():
            if debug: log("plugin info found in config file")
            if 'data_url' in config_plugin:
                # get the data url for the plugin
                data_url = config_plugin['data_url']
                log("   getting data from cloudcheckr")
                # get the report data from cloudcheckr which is by tag
                data = cloudcheckr.loadData(data_url, days_to_report, "Groupings", debug)
            elif 'aws_ce' in config_plugin:
                group_by_tag = None
                if 'group_by_tag' in config_plugin['aws_ce']:
                    group_by_tag = config_plugin['aws_ce']['group_by_tag']
                group_by = None
                if group_by_tag:
                    group_by = [
                        {
                            "Type": "TAG",
                            "Key": group_by_tag
                        }
                    ]
                granularity = 'DAILY'
                if 'filter' in config_plugin['aws_ce']:
                    filter = config_plugin['aws_ce']['filter']
                if group_by_tag and filter:
                    # get the report data from aws cost explorer
                    log("   getting data from aws using cost explorer")
                    data = aws_cost_collector.get_costs(days_to_report=days_to_report,
                                                        granularity=granularity,
                                                        filter=filter,
                                                        group_by=group_by,
                                                        debug=debug)
                    # We need to convert this to cloudcheckr format
                    data = cloudcheckr.convert(data, group_by_tag, debug)

    if data:
        tag_to_match = None
        if debug: log("%i tags returned" % len(data['Groupings']))

        # Find our team info in the config file
        for team in configMap['teams']:
            if team['name'] == team_name:
                team_members = team['members']
                tag_to_match = team[id()]['include_tag']

        if debug: log("Looking in report data for tag name %s" % tag_to_match)

        # look in the data from the report for a tag value matching that we are looking for
        for tag in data['Groupings']:
            # Assume the memberID/email in the config file is lower case
            member_id = str(tag['Name'].split(tag_to_match)[1]).strip().lower()
            if debug: log("member_id in report data is %s" % member_id)
            if member_id in team_members:
                if debug: log("team member found in report data: %s" % member_id)

                # Now we can get their cost from the report data
                totalCost = 0
                for costitem in tag['Costs']:
                    totalCost = totalCost + costitem['Amount']

                if debug: log("total cost for %s is %s" % (member_id,totalCost))

                team_cost['individual'][member_id] = format(float(totalCost),'.2f')

    return team_cost
