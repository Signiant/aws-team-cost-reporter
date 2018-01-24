import urllib2
import json
import logging
from jsonmerge import Merger
import datetime


def id():
    return "cloudcheckr"


def log (message):
    print id() + ": " + message


def getStartEndFilterString(number_of_days):
    ''' get the start and end filter string based on the number of days to report '''
    now = datetime.datetime.now()
    n_days_ago = now - datetime.timedelta(days=number_of_days)

    current_date_str = now.strftime("%Y-%m-%d")
    n_days_ago_str = n_days_ago.strftime("%Y-%m-%d")

    # return start=2016-06-01&end=2016-06-30
    start_end_string = "start=" + n_days_ago_str + "&end=" + current_date_str

    return start_end_string


def loadData(base_url,days_to_report,merge_field = "Groupings",debug=False):
    moreData = True
    data = None
    data_full = dict()
    records_read = 100

    # Add date filters to the url
    date_filter_url = base_url + "&" + getStartEndFilterString(days_to_report)

    # We need to handle merging the data into one response
    # https://pypi.python.org/pypi/jsonmerge

    schema = json.loads('{ "properties": { "' + merge_field + '": { "mergeStrategy": "append"}}}')
    if debug: log("schema is %s" % schema)
    merger = Merger(schema)

    calling_url = date_filter_url
    while moreData:
        if debug: log("Calling URL %s" % str(calling_url))
        try:
            response = urllib2.urlopen(calling_url)
            data = json.loads(response.read())
        except urllib2.URLError as e:
            log("ERROR: Unable to open URL %s : %s" % (date_filter_url,e.reason))

        # Merge the results...needed if the data is paginated.
        if data:
            data_full = merger.merge(data_full,data)

        # Result data could be paginated
        # See http://support.cloudcheckr.com/cloudcheckr-api-userguide/
        if data and 'HasNext' in data and data['HasNext'] == True:
            log("Read %s records.  More data to read" % records_read)
            if debug: log("more data to read")
            calling_url = date_filter_url + "&next_token=" + data['NextToken']
            records_read = records_read+100
        else:
            moreData = False

    return data_full


def convert(cost_data, tag, debug=False):
    return_data = {}
    totals = {}
    total = 0
    count = 0
    min = 0
    max = 0

    # Grouping by tag results in a key with the tag name plus a $
    tag_split = tag + '$'

    # Temporary dict used for storing groupings based on tag
    tag_dict = {}

    # Each element in the cost_data list is for a particular day
    for time_period in cost_data:
        date_entry = time_period['TimePeriod']['Start'] + 'T00:00:00'
        for group in time_period['Groups']:
            key = group['Keys'][0]
            if debug: log('Key: %s' % key)
            if not key.split(tag_split)[1]:
                tag_value = tag + ' untagged'
            else:
                tag_value = tag + ' ' + key.split(tag_split)[1]
            amount = float(group['Metrics']['BlendedCost']['Amount'])
            if count == 0:
                # Set an initial min amount
                min = amount
            total += amount
            count += 1
            if amount > max:
                max = amount
            if amount < min:
                min = amount
            cost_entry = {"Date": date_entry, "Amount": amount, "UsageQuantity": 0.0}
            if tag_value in tag_dict:
                # Already have a dict entry for this tag_value - append another item to the list
                tag_dict[tag_value].append(cost_entry)
            else:
                # No entry for this tag_value - start a new list
                tag_dict[tag_value] = [cost_entry]

    # At this point, tag_dict is a dict with keys for each unique tag_value
    # eg.
    # {
    #     "acme:email user1@domain" : [
    #         {
    #            "Date": "2018-01-01T00:00:00",
    #            "Amount": float,
    #            "UsageQuantity": 0.0
    #         },
    #         {
    #            "Date": "2018-01-02T00:00:00",
    #            "Amount": float,
    #            "UsageQuantity": 0.0
    #         }
    #     ],
    #     "acme:email user2@domain" : [
    #         {
    #            "Date": "2018-01-01T00:00:00",
    #            "Amount": float,
    #            "UsageQuantity": 0.0
    #         },
    #         {
    #            "Date": "2018-01-02T00:00:00",
    #            "Amount": float,
    #            "UsageQuantity": 0.0
    #         }
    #     ]
    # }
    # Need the following format:
    # Format:
    # {
    #    "Total": float, "Max": float, "Min": float, "Average": float,
    #    "Groupings": [
    #       {
    #          "Name": "acme:email user1@domain.com",
    #          "Costs": [
    #             {
    #                "Date": "2018-01-01T00:00:00",
    #                "Amount": float,
    #                "UsageQuantity": 0.0
    #             },...
    #          ]
    #       },...
    #   ]
    # }

    groupings = []
    for unique_tag in tag_dict:
        group_entry = {}
        group_entry['Name'] = unique_tag
        group_entry['Costs'] = tag_dict[unique_tag]
        groupings.append(group_entry)

    return_data['Total'] = total
    return_data['Max'] = max
    return_data['Min'] = min
    return_data['Average'] = total / count
    return_data['Groupings'] = groupings
    return return_data