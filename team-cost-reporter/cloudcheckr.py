import urllib2,json
from jsonmerge import Merger

def id():
    return "cloudcheckr"

def log (message):
    print id() + ": " + message

# get the start and end filter string based on the number of days to report
def getStartEndFilterString(number_of_days):
    start_end_string = ""

    return start_end_string

def loadData(url,days_to_report,merge_field = "Groupings",debug=False):
    moreData = True
    base_url = url
    data = None
    data_full = dict()
    records_read = 100

    # We need to handle merging the data into one response
    # https://pypi.python.org/pypi/jsonmerge

    schema = json.loads('{ "properties": { "' + merge_field + '": { "mergeStrategy": "append"}}}')
    if debug: log("schema is %s" % schema)
    merger = Merger(schema)

    while moreData:
        if debug: log("Calling URL %s" % str(url))
        try:
            response = urllib2.urlopen(url)
            data = json.loads(response.read())
        except urllib2.URLError as e:
            log("ERROR: Unable to open URL %s : %s" % (url,e.reason))

        # Merge the results...needed if the data is paginated.
        if data:
            data_full = merger.merge(data_full,data)

        # Result data could be paginated
        # See http://support.cloudcheckr.com/cloudcheckr-api-userguide/
        if data and 'HasNext' in data and data['HasNext'] == True:
            log("Read %s records.  More data to read" % records_read)
            if debug: log("more data to read")
            url = base_url + "&next_token=" + data['NextToken']
            records_read = records_read+100
        else:
            moreData = False

    return data_full
