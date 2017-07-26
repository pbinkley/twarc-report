#!/usr/bin/env python

import os
import sys
import argparse
import json
import errno
import time
from twarc import Twarc

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

lastid = "0"
lastidfile = os.path.join(data_dir, "last-id")
if os.path.exist(lastidfile)
    try:
        with open(lastidfile) as lastid_data:
            lastid = lastid_data.read().strip()
            lastid_data.close()
    except:
        print("Cannot read last-id file " + lastidefile)
`
timestr = time.strftime("%Y%m%d-%H%M%S")
tweetsfile = os.path.join(tweets_dir, "tweets-" + timestr + ".json")
output = open(tweetsfile, "w")

t = Twarc() # it will get credentials from env vars or .twarc file
tweetcount = 0
lasttweet = lastid
for tweet in t.search(metadata["search"], since_id=lastid):
    # TODO implement other parameters for search
    output.write(tweet)
    if tweetcount == 0:
        lasttweet = tweet["id_str"]
    tweetcount = tweetcount + 1

output.close()

if lasttweet != lastid:
    output = open(os.path.join(data_dir, "last-id"), "w")
    output.write(lasttweet)
    output.close()

print("Harvested " + str(tweetcount) + " tweets (up to " + lasttweet + ") into " + tweetsfile)
