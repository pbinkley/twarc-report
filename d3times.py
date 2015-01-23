#!/usr/bin/env python

import sys
import json
import optparse
import fileinput
import datetime
import dateutil.parser # $ pip install python-dateutil
import pytz # $ pip install pytz
from tzlocal import get_localzone # $ pip install tzlocal
import d3json # local module
from profiler import Profiler # local module
import ast
import re

class TimeProfiler(Profiler):
    # interval, in milliseconds
    intervalFormats = {
        "S": {"name": "second", "format": "%Y-%m-%d %H:%M:%S", "interval": 1000},
        "M": {"name": "minute", "format": "%Y-%m-%d %H:%M", "interval":  1000 * 60},
        "H": {"name": "hour", "format": "%Y-%m-%d %H", "interval":  1000 * 60 * 60},
        "d": {"name": "day", "format": "%Y-%m-%d", "interval":  1000 * 60 * 60 * 24},
        "m": {"name": "month", "format": "%Y-%m", "interval":  1000 * 60 * 60 * 24 * 28},
        "Y": {"name": "year", "format": "%Y-%m", "interval":  1000 * 60 * 60 * 24 * 365}
    }
    def __init__(self, opts):
        Profiler.__init__(self, opts)
        try:
            self.intervalParts = re.search("([0-9]*)([^0-9]*)", self.intervalStr)
            if self.intervalParts.group(1) == "":
                self.intervalCount = 1
            else:
                self.intervalCount = int(self.intervalParts.group(1))
            self.intervalUnit = self.intervalParts.group(2)
            self.interval = self.intervalCount * self.intervalFormats[self.intervalUnit]["interval"]
            self.format = self.intervalFormats[self.intervalUnit]["format"]
            self.intervalLabel = str(self.intervalCount) + " " + self.intervalFormats[self.intervalUnit]["name"]
            if self.intervalCount > 1:
                self.intervalLabel += "s"

        except ValueError as e:
            sys.stderr.write("uhoh: %s\n" % e)

        # gather in a dict with count if aggregating, otherwise in a list
        if aggregate:
            self.items = {}
        else:
            self.items = []

    def process(self, tweet):
        Profiler.process(self, tweet)
        created_at = dateutil.parser.parse(tweet["created_at"])
        local_dt = self.tz.normalize(created_at.astimezone(tz))
        if self.intervalStr != '':
            if self.intervalUnit == "S":
                local_dt = local_dt - datetime.timedelta(seconds=local_dt.second % int(self.intervalCount))
            elif self.intervalUnit == "M":
                local_dt = local_dt - datetime.timedelta(minutes=local_dt.minute % int(self.intervalCount))
            elif self.intervalUnit == "H":
                local_dt = local_dt - datetime.timedelta(hours=local_dt.hour % int(self.intervalCount))
        # otherwise use format to aggregate values - though this treats intervalCount as 1
        result = local_dt.strftime(self.format)
        if self.aggregate:
            self.items[result] = self.items.get(result, 0) + 1
        else:
            self.items.append(result)
            
    def report(self):
        profile = Profiler.report(self)
        if self.output == "csv":
            if aggregate:
                values = d3json.namevaluecsv(self.items)
            else:
                values = d3json.valuecsv(self.items)
            return values
        else:
            if aggregate:
                values = d3json.namevaluejson(self.items)
            else:
                values = d3json.valuejson(self.items)
            return {"profile": profile, "values": values}


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
    d3json.embed(opts.template, data)
else:
    print data

