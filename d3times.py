#!/usr/bin/env python

import sys
import json
import optparse
import fileinput
import datetime
import dateutil.parser # $ pip install python-dateutil
import pytz # $ pip install pytz
from tzlocal import get_localzone # $ pip install tzlocal
import d3output # local module
from profiler import TimeProfiler # local module
import ast
import re

opt_parser = optparse.OptionParser()
opt_parser.add_option('-t', '--timezone', type=str, default="", 
    help='output timezone (e.g. "America/New_York" or "local"; default: UTC)')
opt_parser.add_option('-a', '--aggregate', action='store_true', default=False, 
    help="Aggregate the values to produce key-value pairs with counts")
opt_parser.add_option("-o", "--output", dest="output", type="str", 
    help="embed | csv | json (default: embed)", default="embed")
opt_parser.add_option("-p", "--template", dest="template", type="str", 
    help="name of template in utils/template (default: timebar.html)", default="timebar.html")
opt_parser.add_option("-i", "--interval", dest="intervalStr", type="str", 
    help="interval for grouping timestamps, in seconds, minutes or hours, e.g. 15m (default: 1S)", default="1S")

opts, args = opt_parser.parse_args()
# prepare to serialize opts and args as json
# converting opts to str produces string with single quotes,
# but json requires double quotes
optsdict = ast.literal_eval(str(opts))
argsdict = ast.literal_eval(str(args))

aggregate = opts.aggregate
tzname = opts.timezone

# determine output time zone
if tzname == "":
    tz = pytz.UTC
elif tzname == "local":
    tz = get_localzone() # system timezone, from tzlocal
else: 
    tz = pytz.timezone(tzname)

# if an interval is provided in the options, use it; otherwise
# determin the interval from the datetime format
intervalStr = opts.intervalStr # e.g. 15m

profiler = TimeProfiler({
    "tz": tz, 
    "output": opts.output, 
    "aggregate": aggregate, 
    "intervalStr": intervalStr})

for line in fileinput.input(args):
    try:
        tweet = json.loads(line)
        profiler.process(tweet)
    except ValueError as e:
        sys.stderr.write("uhoh: %s\n" % e)

data = profiler.report()
optsdict["interval"] = profiler.interval
optsdict["format"] = profiler.format
optsdict["intervalLabel"] = profiler.intervalLabel

if type(data) is dict:
    data["opts"] = optsdict
    data["args"] = argsdict
    
if opts.output == "embed":
    d3output.embed(opts.template, data)
else:
    print data

