import urllib2,json
from jsonmerge import Merger

def id():
    return "cloudcheckr"

def log (message):
    print id() + ": " + message

def loadData(url,merge_field = "Groupings",debug=False):
    moreData = True
    base_url = url
    data = None
    data_full = dict()

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
            if debug: log("more data to read")
            url = base_url + "&next_token=" + data['NextToken']
        else:
            moreData = False

    return data_full
