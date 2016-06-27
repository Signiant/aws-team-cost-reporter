import json

# Project modules
import cloudcheckr

def id():
    return "dynamodb"

def log (message):
    print id() + ": " + message

#
# We need this here because the data from cloudcheckR is incorrect
# When cloudcheckr is fixed, this is no longer needed
#
def getDailyTableCost(prov_read,prov_write,storage):
    table_cost = 0.0

    # Costs are here: https://aws.amazon.com/dynamodb/pricing/
    one_write_cost = 0.0065 / 10
    one_read_cost = 0.0065 / 50
    storage_cost = 0.25 / 30

    total_write_cost = prov_write * one_write_cost * 24
    total_read_cost = prov_read * one_read_cost * 24
    total_storage_cost = (storage /1024/1024/1024) * storage_cost

    table_cost = total_write_cost + total_read_cost + total_storage_cost

    return float(table_cost)

def getTeamCost(team_name,configMap,debug):
    team_cost = dict(shared=dict())
    data_url = ''
    data = ''
    totalCost = 0
    days_to_report = configMap['global']['days_to_report']

    log("getting team cost for team: %s for %i days" % (team_name,days_to_report))

    # get the data url for the dynamodb plugin url
    for config_plugin in configMap['plugins']:
        if config_plugin['name'] == id():
            if debug: log("plugin info found in config file")
            data_url = config_plugin['data_url']

    if data_url:
        data = cloudcheckr.loadData(data_url,days_to_report,"DynamoDbDetails",debug)

        if data:
            if debug: log("%i tables returned" % len(data['DynamoDbDetails']))

            # Find our team info in the config file
            for team in configMap['teams']:
                if team['name'] == team_name:
                    config_tables = team['dynamodb']['tables']

            # Check each table or table prefix in the config file
            for config_match_table in config_tables:
                log("looking for table %s in cloudcheckr data" % config_match_table)

                # Now compare each table in the config to the cloudcheckr data
                for cc_table in data['DynamoDbDetails']:
                    cc_table_name = str(cc_table['TableName'])

                    # CloudcheckR has a bug where these are all zero.  Until fixed, use this function
                    #cc_table_cost = cc_table['ProvisionedThroughputReadCost'] + cc_table['ProvisionedThroughputWriteCost'] + cc_table['StorageCost']
                    cc_table_cost = getDailyTableCost(cc_table['ProvisionedThroughputRead'],cc_table['ProvisionedThroughputWrite'],cc_table['TableSizeBytes']) * days_to_report

                    if debug: log("Daily cost for %s = %s" % (cc_table_name, str(cc_table_cost)))
                    if debug: log("CC Table name %s. Looking for %s" % (cc_table_name, config_match_table))

                    # Are we looking for a prefix?
                    if str(config_match_table).endswith("*"):
                        prefix = config_match_table.split("*")[0]
                        if debug: log("wildcard match - prefix %s" % prefix)

                        if cc_table_name.lower().startswith(prefix.lower()):
                            if debug: log("Wildcard match found")
                            totalCost = float(totalCost) + float(cc_table_cost)
                    else:
                        # This is not a wildcard so only match exact table name
                        if cc_table_name.lower() == str(config_match_table).lower():
                            if debug: log("Exact match found")
                            totalCost = float(totalCost) + float(cc_table_cost)

            team_cost['shared']['tables'] = format(float(totalCost),'.2f')

    return team_cost
