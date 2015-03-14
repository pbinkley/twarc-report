#!/usr/bin/env python

import os
import sys
import argparse
import json
import errno

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

parser = argparse.ArgumentParser("harvest")
parser.add_argument("archive_dir", action="store",
                    help="a directory where results are stored")
args = parser.parse_args()

if not os.path.isdir(args.archive_dir):
    sys.exit("Directory " + args.archive_dir + " does not exist.")
    
data_dir = os.path.join(args.archive_dir, "data")
make_sure_path_exists(data_dir)
tweets_dir = os.path.join(data_dir, "tweets")
make_sure_path_exists(tweets_dir)

metadatafile = os.path.join(args.archive_dir, "metadata.json")
try:
    with open(metadatafile) as json_data:
        metadata = json.load(json_data)
        json_data.close()
except:
    sys.exit("Cannot read metadata file " + metadatafile)

sys.argv = ["", metadata["search"], tweets_dir]
sys.path.append("twarc")
sys.path.append("twarc/utils")
import archive
archive.main()
