import logging
import boto3
# Project modules
import cloudcheckr

logging.getLogger('botocore').setLevel(logging.CRITICAL)


def id():
    return "dynamodb"


def log (message):
    print id() + ": " + message


def _get_table_names(dynamodb_client, start_name=None, debug=False):
    result = []
    if start_name:
        query_result = dynamodb_client.list_tables(ExclusiveStartTableName=start_name)
    else:
        query_result = dynamodb_client.list_tables()
    if 'ResponseMetadata' in query_result and query_result['ResponseMetadata']['HTTPStatusCode'] == 200:
        if 'LastEvaluatedTableName' in query_result:
            last_table_name = query_result['LastEvaluatedTableName']
            if debug:
                log(query_result['TableNames'])
                log("More results to come...")
            result.extend(query_result['TableNames'])
            result.extend(_get_table_names(dynamodb_client=dynamodb_client,
                                      start_name=query_result['LastEvaluatedTableName'],
                                      debug=debug))
        else:
            if debug: log(query_result['TableNames'])
            result.extend(query_result['TableNames'])
    return result


def _get_table_details(dynamodb_client, table_name, debug=False):
    result = {}
    result['TableName'] = table_name
    query_result = dynamodb_client.describe_table(TableName=table_name)
    if 'Table' in query_result:
        result['TableSizeBytes'] = query_result['Table']['TableSizeBytes']
        provisioned_table_throughput_read = query_result['Table']['ProvisionedThroughput']['ReadCapacityUnits']
        provisioned_table_throughput_write = query_result['Table']['ProvisionedThroughput']['WriteCapacityUnits']
        if 'GlobalSecondaryIndexes' in query_result['Table']:
            for gsi in query_result['Table']['GlobalSecondaryIndexes']:
                provisioned_table_throughput_read += gsi['ProvisionedThroughput']['ReadCapacityUnits']
                provisioned_table_throughput_write += gsi['ProvisionedThroughput']['WriteCapacityUnits']
        result['ProvisionedThroughputRead'] = provisioned_table_throughput_read
        result['ProvisionedThroughputWrite'] = provisioned_table_throughput_write
    return result


def _get_table_info_from_region(account_creds, region, debug=False):
    table_list = []
    if 'profile_name' in account_creds:
        SESSION = boto3.session.Session(profile_name=account_creds['profile_name'], region_name=region)
    elif 'aws_access_key_id' in account_creds and 'aws_secret_access_key' in account_creds:
        SESSION = boto3.session.Session(aws_access_key_id=account_creds['aws_access_key_id'],
                                        aws_secret_access_key=account_creds['aws_secret_access_key'],
                                        region_name=region)
    else:
        log('Invalid credentials provided - cannot get DynamoDB data')
        return table_list
    DYNAMODB = SESSION.client('dynamodb')
    # Get the list of table names in this region
    table_name_list = _get_table_names(DYNAMODB, debug=debug)
    # Get the provisioned throughput and table size for each table
    for table in table_name_list:
        table_list.append(_get_table_details(DYNAMODB, table, debug))
    return table_list


def _get_table_info(account_creds, region_list, debug=False):
    account_dynamo_details = []
    for region in region_list:
        account_dynamo_details.extend(_get_table_info_from_region(account_creds, region))
    return account_dynamo_details


def get_table_info(account_list, debug=False):
    dynamo_db_details = []
    for account in account_list:
        account_creds = account['credentials']
        region_list = account['regions']
        dynamo_db_details.extend(_get_table_info(account_creds, region_list, debug))
    return {'DynamoDbDetails': dynamo_db_details}


def getDailyTableCost(prov_read,prov_write,storage):
    '''
    We need this here because the data from cloudcheckR is incorrect
    When cloudcheckr is fixed, this is no longer needed
    :param prov_read: provisioned read throughput
    :param prov_write: provisioned write throughput
    :param storage: size of the table in bytes
    :return: cost for the table
    '''
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

    data = None
    for config_plugin in configMap['plugins']:
        if config_plugin['name'] == id():
            if debug: log("plugin info found in config file")
            if 'data_url' in config_plugin:
                # get the data url for the plugin
                data_url = config_plugin['data_url']
                log("   getting data from cloudcheckr")
                # get the report data from cloudcheckr
                data = cloudcheckr.loadData(data_url, days_to_report, "DynamoDbDetails", debug)
            elif 'aws_dynamodb' in config_plugin:
                # Get the data from the aws_dynamodb entry
                account_list = config_plugin['aws_dynamodb']['accounts']
                # PLEASE NOTE: Data obtained is for this point in time - it doesn't take in account an average
                # over the time period for something like autoscaling of throughput or changes in table size
                # Same limitation applies equally to the cloudcheckr data, so we're no worse off...
                data = get_table_info(account_list, debug)

    if data:
        if debug: log("%i tables returned" % len(data['DynamoDbDetails']))

        # Find our team info in the config file
        for team in configMap['teams']:
            if team['name'] == team_name:
                config_tables = team[id()]['tables']

        # Check each table or table prefix in the config file
        for config_match_table in config_tables:
            log("looking for table %s in report data" % config_match_table)

            # Now compare each table in the config to the report data
            for cc_table in data['DynamoDbDetails']:
                cc_table_name = str(cc_table['TableName'])

                cc_table_cost = getDailyTableCost(cc_table['ProvisionedThroughputRead'],cc_table['ProvisionedThroughputWrite'],cc_table['TableSizeBytes']) * days_to_report

                if debug: log("Daily cost for %s = %s" % (cc_table_name, str(cc_table_cost)))
                if debug: log("CC Table name %s. Looking for %s" % (cc_table_name, config_match_table))

                # Are we looking for a wildcard match or exact match?
                match = False
                if str(config_match_table).startswith("*") and str(config_match_table).endswith("*"):
                    contain_match = config_match_table.split("*")[1]
                    if debug: log("wildcard matching- contains %s" % contain_match)

                    if contain_match.lower() in cc_table_name.lower():
                        if debug: log("Contains match found")
                        match = True
                elif str(config_match_table).endswith("*"):
                    prefix = config_match_table.split("*")[0]
                    if debug: log("wildcard matching - prefix %s" % prefix)

                    if cc_table_name.lower().startswith(prefix.lower()):
                        if debug: log("Wildcard prefix match found")
                        match = True
                elif str(config_match_table).startswith("*"):
                    suffix = config_match_table.split("*")[1]
                    if debug: log("wildcard matching - suffix %s" % suffix)

                    if cc_table_name.lower().endswith(suffix.lower()):
                        if debug: log("Wildcard suffix match found")
                        match = True
                elif config_match_table == cc_table_name:
                    if debug: log("Exact matching")
                    match = True

                if match:
                    totalCost = float(totalCost) + float(cc_table_cost)
                    if debug: log("total cost for %s is %s" % (cc_table_name,totalCost))

                    team_cost['shared'][cc_table_name] = format(float(totalCost),'.2f')
                    totalCost = 0

    return team_cost
