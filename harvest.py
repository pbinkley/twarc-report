#!/usr/bin/env python

import os
import sys
import argparse
import json

parser = argparse.ArgumentParser("harvest")
parser.add_argument("archive_dir", action="store",
                    help="a directory where results are stored")
args = parser.parse_args()

if not os.path.isdir(args.archive_dir):
    sys.exit("Directory " + args.archive_dir + " does not exist.")

metadatafile = os.path.join(args.archive_dir, "metadata.json")
try:
    with open(metadatafile) as json_data:
        metadata = json.load(json_data)
        json_data.close()
except:
    sys.exit("Cannot read metadata file " + metadatafile)

sys.argv = ["", metadata["search"], args.archive_dir]
sys.path.append("twarc")
sys.path.append("twarc/utils")
import archive
archive.main()