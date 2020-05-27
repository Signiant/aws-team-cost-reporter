# Project modules
import aws_cost_collector
import cloudcheckr


def id():
    return "eb"


def log(message):
    print(id() + ": " + message)


def getTeamCost(team_name,configMap,debug):
    team_cost = dict(shared=dict())
    data_url = ''
    data = ''
    tag_to_match = ''
    totalCost = 0
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
        if debug: log("%i tags returned" % len(data['Groupings']))

        # Find our team info in the config file
        for team in configMap['teams']:
            if team['name'] == team_name:
                team_members = team['members']
                tag_to_match = team[id()]['include_tag']
                config_envs = team[id()]['envs']

        for config_match_env in config_envs:
            log("looking for eb env %s in report data" % config_match_env)

            for cc_env in data['Groupings']:
                tag_value = cc_env['Name'].split(tag_to_match)
                if debug: log("tag_value: " + str(tag_value))

                if len(tag_value) == 2:
                    cc_env_name = str(tag_value[1].strip().lower())
                else:
                    continue

                if debug: log("eb env in report data is %s" % cc_env_name)

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
                elif config_match_env.lower() == cc_env_name.lower():
                    if debug: log("Exact matching")
                    match = True

                if match:
                    # Match found - add cost
                    if debug: log("*** Matching eb env found")
                    for costitem in cc_env['Costs']:
                        totalCost = totalCost + costitem['Amount']

                        if debug: log("total cost for %s is %s" % (cc_env_name,totalCost))

                    team_cost['shared'][cc_env_name] = format(float(totalCost),'.2f')
                    totalCost = 0

    return team_cost
