import urllib2,json
from jsonmerge import Merger
import datetime

def id():
    return "cloudcheckr"

def log (message):
    print id() + ": " + message

# get the start and end filter string based on the number of days to report
def getStartEndFilterString(number_of_days):
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
