import logging
import datetime
import boto3

logging.getLogger('botocore').setLevel(logging.CRITICAL)


def id():
    return "aws_cost_collector"


def log (message):
    print id() + ": " + message


def get_start_end_strings(number_of_days):
    ''' get the start and end date strings based on the number of days to report '''
    now = datetime.datetime.now()
    n_days_ago = now - datetime.timedelta(days=number_of_days)

    current_date_str = now.strftime("%Y-%m-%d")
    n_days_ago_str = n_days_ago.strftime("%Y-%m-%d")

    # start=2016-06-01
    # end=2016-06-30
    start_string = n_days_ago_str
    end_string = current_date_str
    return (start_string,end_string)


def _get_costs(ce_client, days_to_report, granularity, filter, group_by, next_token=None, debug=False):
    result = []
    start_date, end_date = get_start_end_strings(days_to_report)
    time_period = {'Start': start_date, 'End': end_date}
    metrics = ['UnblendedCost', 'BlendedCost', 'UsageQuantity']
    if next_token:
        if filter:
            query_result = ce_client.get_cost_and_usage(TimePeriod=time_period,
                                                        Granularity=granularity,
                                                        Filter=filter,
                                                        Metrics=metrics,
                                                        GroupBy=group_by,
                                                        NextPageToken=next_token)
        else:
            query_result = ce_client.get_cost_and_usage(TimePeriod=time_period,
                                                        Granularity=granularity,
                                                        Metrics=metrics,
                                                        GroupBy=group_by,
                                                        NextPageToken=next_token)
    else:
        if filter:
            query_result = ce_client.get_cost_and_usage(TimePeriod=time_period,
                                                        Granularity=granularity,
                                                        Filter=filter,
                                                        Metrics=metrics,
                                                        GroupBy=group_by)
        else:
            query_result = ce_client.get_cost_and_usage(TimePeriod=time_period,
                                                        Granularity=granularity,
                                                        Metrics=metrics,
                                                        GroupBy=group_by)
    if 'ResultsByTime' in query_result:
        if 'NextPageToken' in query_result:
            if debug:
                log(query_result['ResultsByTime'])
                log("More results to come...")
            result.extend(query_result['ResultsByTime'])
            result.extend(_get_costs(ce_client=ce_client,
                                     days_to_report=days_to_report,
                                     granularity=granularity,
                                     filter=filter,
                                     group_by=group_by,
                                     next_token=query_result['NextPageToken'],
                                     debug=debug))
        else:
            if debug: log(query_result['ResultsByTime'])
            result.extend(query_result['ResultsByTime'])

    return result


def get_costs(days_to_report, granularity, filter, group_by, debug=False):
    SESSION = boto3.session.Session()
    CE = SESSION.client('ce')
    return _get_costs(ce_client=CE,
                      days_to_report=days_to_report,
                      granularity=granularity,
                      filter=filter,
                      group_by=group_by,
                      next_token=None,
                      debug=debug)
