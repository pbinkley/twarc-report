#!/usr/bin/env python            

import json
import fileinput
import sys
import optparse
from profiler import Profiler # local module
import dateutil.parser # $ pip install python-dateutil
import sparkline

opt_parser = optparse.OptionParser()
opt_parser.add_option("-o", "--output", dest="output", type="str", 
    help="text | json (default: json)", default="json")
opts, args = opt_parser.parse_args()

profiler = Profiler({"extended": True, "blocks": ["all"]})

for line in fileinput.input(args):
    try:
        tweet = json.loads(line)
        profiler.process(tweet)
    except ValueError as e:
        sys.stderr.write("uhoh: %s\n" % e)

data = profiler.report()

if (opts.output == "json"):
    print data
else:
    print "Count:            " + '{:>9}'.format(str(data["count"]))
    print "Users:            " + '{:>9}'.format(str(data["usercount"]))
    print "User percentiles: " + sparkline.sparkify(data["userspercentiles"])
    print "                  " + str(data["userspercentiles"])
    print "Has hashtag:      " + '{:>9}'.format(str(data["hashtagcount"])) + " (" + str("%.2f" % (float(data["hashtagcount"]) / float(data["count"]) * 100.0)) + "%)"
    print "Hashtags:         " + '{:>9}'.format(str(data["hashtags"]))
    print "Hashtags percentiles: " + sparkline.sparkify(data["hashtagspercentiles"])
    print "                  " + str(data["hashtagspercentiles"])
    print "Has URL:          " + '{:>9}'.format(str(data["urlcount"])) + " (" + str("%.2f" % (float(data["urlcount"]) / float(data["count"]) * 100.0)) + "%)"
    print "URLs:             " + '{:>9}'.format(str(data["urls"]))
    print "URLs percentiles: " + sparkline.sparkify(data["urlspercentiles"])
    print "                  " + str(data["urlspercentiles"])
    print "Has Image URL:    " + '{:>9}'.format(str(data["imageurlcount"])) + " (" + str("%.2f" % (float(data["imageurlcount"]) / float(data["count"]) * 100.0)) + "%)"
    print "Image URLs:       " + '{:>9}'.format(str(data["imageurls"]))
    print "Image URLs percentiles: " + sparkline.sparkify(data["imageurlspercentiles"])
    print "                  " + str(data["imageurlspercentiles"])
    print "Retweets:         " + '{:>9}'.format(str(data["retweetcount"])) + " (" + str("%.2f" % (float(data["retweetcount"]) / float(data["count"]) * 100.0)) + "%)"
    print "Geo:              " + '{:>9}'.format(str(data["geocount"])) + " (" + str("%.2f" % (float(data["geocount"]) / float(data["count"]) * 100.0)) + "%)"
    print "Earliest:         " + str(data["earliest"])
    print "Latest:           " + str(data["latest"])
    print "Duration:         " + str(dateutil.parser.parse(data["latest"]) - dateutil.parser.parse(data["earliest"]))

    print "Top users:        " + sparkline.sparkify([u["value"] for u in data["topusers"]]).encode("utf-8")
    for user in data["topusers"]:
        print "{:>7}".format(str(user["value"])) + " " + user["name"]
    print "Top hashtags:     " + sparkline.sparkify([u["value"] for u in data["tophashtags"]]).encode("utf-8")
    for hashtag in data["tophashtags"]:
        print "{:>7}".format(str(hashtag["value"])) + " " + hashtag["name"]
    print "Top URLs:         " + sparkline.sparkify([u["value"] for u in data["topurls"]]).encode("utf-8")
    for url in data["topurls"]:
        print "{:>7}".format(str(url["value"])) + " " + url["name"]
    print "Top Image URLs:   " + sparkline.sparkify([u["value"] for u in data["topimageurls"]]).encode("utf-8")
    for imageurl in data["topimageurls"]:
        print "{:>7}".format(str(imageurl["value"])) + " " + imageurl["name"]
