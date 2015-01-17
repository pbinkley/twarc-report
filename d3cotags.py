#!/usr/bin/env python

import json
import itertools
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-e', '--exclude', type=str, default="", required=False, 
	help='comma-separated list of hashtags to exclude')
parser.add_argument('-o', '--otherize', type=int, default=0, required=False, 
	help='threshold below which to treat hashtags as "other"')
parser.add_argument('-r', '--reciprocal', type=bool, default=False, required=False,
	help='add recciprocal links for each pair')
parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin, 
	help="file of tweets")
args = parser.parse_args()

otherize = args.otherize
exclude = set(args.exclude.lower().split(","))
reciprocal = args.reciprocal

counts = {}
savetweets = []
keepers = set()
	
# gather counts for individual tags	
for line in args.infile:
	try:
		tweet = json.loads(line)
	except:
		continue

	savetweet = []
	for tag in tweet['entities']['hashtags']:
		savetweet.append(tag)
		t = tag['text'].lower()
		counts[t] = counts.get(t, 0) + 1

	savetweets.append(savetweet)

args.infile.close()

# for tags below the threshold, replace with "$other"
# which is not necessary is otherize=0
if otherize > 0:
	countkeys = counts.keys()
	for count in countkeys:
		if counts[count] < otherize:
			counts['$other'] = counts.get('$other', 0) + counts[count]
			del counts[count]
		else:
			keepers.add(count)
	
# now process hashtags again, replacing any tag not in keepers with $other
counts = {}
for savetweet in savetweets:

	# cleantags gathers unique, lower-cased tags
	cleantags = set()

	for hashtag in savetweet:
		t = hashtag['text'].lower()
		if otherize == 0 or t in keepers:
			cleantags.add(t)
		else:
			cleantags.add('$other')
    	
	# sort tags and remove tags that are in the exclude set 
	cleantags = sorted(cleantags.difference(exclude))

	# generate all pairs
	for c in itertools.combinations(cleantags, 2):
		t = c[0] + "," + c[1]
		counts[t] = counts.get(t, 0) + 1
		if reciprocal:
			t = c[1] + "," + c[0]
			counts[t] = counts.get(t, 0) + 1

tags = counts.keys()
tags.sort(lambda a, b: cmp(counts[b], counts[a]))

# print csv headers
print "has,prefers,count"
for tag in tags:
    print (tag + "," + str(counts[tag])).encode('utf8')



