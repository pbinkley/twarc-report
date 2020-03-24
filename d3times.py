#!/usr/bin/env python

import optparse
import pytz # $ pip install pytz
from tzlocal import get_localzone # $ pip install tzlocal
import d3output # local module
from profiler import TimeProfiler # local module

opt_parser = optparse.OptionParser()
opt_parser.add_option("-t", "--timezone", type=str, default="",
    help="output timezone (e.g. 'America/New_York' or 'local'; default: UTC)")
opt_parser.add_option('-a', '--aggregate', action='store_true', default=False,
    help="Aggregate the values to produce key-value pairs with counts")
opt_parser.add_option("-o", "--output", dest="output", type="str",
    help="html | csv | json (default: html)", default="html")
opt_parser.add_option("-p", "--template", dest="template", type="str",
    help="name of template in utils/template (default: timebar.html)", default="timebar.html")
opt_parser.add_option("-i", "--interval", dest="intervalStr", type="str",
    help="interval for grouping timestamps, in seconds, minutes or hours, e.g. 15M (default: 1S)", default="1S")

opts, args = opt_parser.parse_args()

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
# determine the interval from the datetime format
intervalStr = opts.intervalStr # e.g. 15M

profiler = TimeProfiler({
    "tz": tz,
    "output": opts.output,
    "aggregate": aggregate,
    "intervalStr": intervalStr})

profiler.gettweets(opts, args)

data = profiler.report()

if opts.output == "html":
    d3output.embed(opts.template, data)
else:
    print(data)
