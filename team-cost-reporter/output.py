import pprint
import json
import mail
import datetime
import os

def id():
    return "output"

def log (message):
    print(id() + ": " + message)

def getPluginFriendlyName(plugin_name,configMap):
    friendly = plugin_name

    for plugin in configMap['plugins']:
        if plugin['name'] == plugin_name:
            if 'friendly_name' in plugin:
                friendly = plugin['friendly_name']

    return friendly

def getToAddr(team_name,configMap):
    to_addr = ""

    # Find our team info in the config file
    for team in configMap['teams']:
        if team['name'] == team_name:
            to_addr = team['email']

    return to_addr

def getEndDate(configMap):
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d")

def getStartDate(configMap):
    number_of_days = configMap['global']['days_to_report']

    now = datetime.datetime.now()
    n_days_ago = now - datetime.timedelta(days=number_of_days)
    return n_days_ago.strftime("%Y-%m-%d")

def writeTeamCosts(team_name,configMap,plugin_results,debug):
    output_folder = "/output"
    output_filename = output_folder + "/" + team_name + ".json"

    # Add the start and end dates to the raw output
    plugin_results['period'] = dict()
    plugin_results['period']['start'] = getStartDate(configMap)
    plugin_results['period']['end'] = getEndDate(configMap)

    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    # Write the file
    log("Writing raw team costs to %s for team %s" % (output_filename,team_name))
    target = open(output_filename, 'w')
    json.dump(plugin_results, target)
    target.close()

def getSharedDetailCosts(configMap,plugin_results,debug):
    items_dict = dict()
    cost_type = "shared"
    table = "<table>"

    table = table + "<tr><th>Service</th><th>Object</th><th>Period Cost</th></tr>"

    for plugin_name in plugin_results:

        if cost_type in plugin_results[plugin_name]:
            table = table + "<tr><td>" + getPluginFriendlyName(plugin_name,configMap) + "</td></tr>"

            items_dict = plugin_results[plugin_name][cost_type]

            for item in sorted(items_dict):
                table = table + "<tr><td></td><td>" + item + "</td><td>$" + items_dict[item] + "</td></tr>"

    table = table + "</table>"

    return table

# This should return a table with the the shared summary
# Which will then be added to the email template
def getSharedSummaryCosts(configMap,plugin_results,debug):
    items_dict = dict()
    cost_type = "shared"
    table = "<table>"

    table = table + "<tr><th>Service</th><th>Period Cost</th></tr>"

    for plugin_name in plugin_results:
        line_item_cost = 0.0
        if cost_type in plugin_results[plugin_name]:
            items_dict = plugin_results[plugin_name][cost_type]

            for item in items_dict:
                line_item_cost = line_item_cost + float(items_dict[item])

            table = table + "<tr><td>" + getPluginFriendlyName(plugin_name,configMap) + "</td><td>$" + "{0:.2f}".format(line_item_cost) + "</td></tr>"

    table = table + "</table>"

    return table

def getIndividualCosts(configMap,plugin_results,debug):
    items_dict = dict()
    cost_type = "individual"
    table = "<table>"

    table = table + "<tr><th>Service</th><th>Person</th><th>Period Cost</th></tr>"

    for plugin_name in plugin_results:

        if cost_type in plugin_results[plugin_name]:
            table = table + "<tr><td>" + getPluginFriendlyName(plugin_name,configMap) + "</td></tr>"

            items_dict = plugin_results[plugin_name][cost_type]

            for item in items_dict:
                table = table + "<tr><td></td><td>" + item + "</td><td>$" + items_dict[item] + "</td></tr>"

    table = table + "</table>"

    return table

def getTotalTeamCost(configMap,plugin_results,debug):
    totalCost = 0.0

    for plugin_name in plugin_results:
        if 'individual' in plugin_results[plugin_name]:
            items_dict = plugin_results[plugin_name]['individual']
        elif 'shared' in plugin_results[plugin_name]:
            items_dict = plugin_results[plugin_name]['shared']

        for item in items_dict:
            totalCost = totalCost + float(items_dict[item])

    return totalCost

# produce an html file and return the filename
def outputResults(team_name,configMap,plugin_results,debug):

    if debug: pprint.pprint(plugin_results)

    # Get the SMTP config
    smtp_server = configMap['global']['smtp']['server']
    smtp_tls = configMap['global']['smtp']['tls']
    smtp_port = configMap['global']['smtp']['port']

    smtp_user = configMap['global']['smtp']['user']
    smtp_pass = configMap['global']['smtp']['password']
    smtp_from = configMap['global']['smtp']['from_addr']
    smtp_cc = configMap['global']['smtp']['cc_addrs']

    email_template_file = configMap['global']['smtp']['template']
    email_to_addr = getToAddr(team_name,configMap)
    email_subject = "Team %s AWS Cost Report for %s to %s" % (team_name,getStartDate(configMap),getEndDate(configMap))

    log("Sending email to %s for team %s" % (email_to_addr,team_name))

    values = {}
    values['teamName'] = team_name
    values['startDate'] = getStartDate(configMap)
    values['endDate'] = getEndDate(configMap)
    values['reportGenerationDate'] = datetime.datetime.now().strftime("%Y-%m-%d")
    values['totalCost'] = "{0:.2f}".format(getTotalTeamCost(configMap,plugin_results,debug))
    values['sharedSummaryCosts'] = getSharedSummaryCosts(configMap,plugin_results,debug)
    values['taggedCosts'] = getIndividualCosts(configMap,plugin_results,debug)
    values['sharedDetailCosts'] = getSharedDetailCosts(configMap,plugin_results,debug)

    template = mail.EmailTemplate(template_name=email_template_file, values=values)
    server = mail.MailServer(server_name=smtp_server, username=smtp_user, password=smtp_pass, port=smtp_port, require_starttls=smtp_tls)

    msg = mail.MailMessage(from_email=smtp_from, to_emails=[email_to_addr], cc_emails=smtp_cc,subject=email_subject,template=template)
    mail.send(mail_msg=msg, mail_server=server)

    # Write the output to disk so other scripts can use it if needed
    writeTeamCosts(team_name,configMap,plugin_results,debug)
