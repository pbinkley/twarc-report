#!/usr/bin/env python            

import json
import optparse
from profiler import Profiler # local module
from dateutil import parser
import sparkline
import os
from mako.template import Template
import glob
import sys
import re
import humanize

opt_parser = optparse.OptionParser()
opt_parser.add_option("-o", "--output", dest="output", type="str", 
    help="text | json | html (default: text)", default="text")
opts, args = opt_parser.parse_args()

profiler = Profiler({"extended": True, "blocks": ["all"]})

profiler.gettweets(opts, args)

data = profiler.report()

if (opts.output == "json"):
    print(json.dumps(data))
elif (opts.output == "html"):
    metadata_file = os.path.join(os.path.dirname(args[0]), "../metadata.json")
    with open(metadata_file) as json_data:
        metadata = json.load(json_data)
        json_data.close()

    data['title'] = metadata['title']
    data['search'] = metadata['search']

    # gather names and sizes of html files
    data['reports'] = []
    p = re.compile('.*\/html\/(.*)\.html')
    for report in sorted(glob.glob(os.path.join(os.path.dirname(args[0]), "../html/*.html"))):
        m = p.match(report)
        size = os.path.getsize(report)
        data['reports'].append({'report': m[1], 'size': humanize.naturalsize(size)})

    mytemplate = Template(filename='templates/reportprofile.html')
    print(mytemplate.render(data = data))
else:
    mytemplate = Template(filename='templates/reportprofile.txt')
    print(mytemplate.render(data = data))
