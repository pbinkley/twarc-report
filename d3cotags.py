#!/usr/bin/env python

import json
import itertools
import fileinput
import sys
import optparse
import d3json # local module
from profiler import Profiler # local module
from collections import Counter
import ast
import dateutil.parser # $ pip install python-dateutil



class CotagsProfiler(Profiler):
    def __init__(self, opts):
        Profiler.__init__(self, opts)
        self.savetweets = []
        self.counts = Counter()
        self.keepers = set()

    def process(self, tweet):
        Profiler.process(self, tweet)
        # gather a list of the tags in this tweet, lowercased
        savetweet = []
        for tag in tweet['entities']['hashtags']:
            savetweet.append(tag)
            t = tag['text'].lower()
            # and increment count for this tag
            self.counts[t] += 1
        # add tag list to savetweets
        self.savetweets.append(savetweet)
        

    def report(self):
        profile = Profiler.report(self)

        # for tags below the "otherize" threshold, replace with "$other"
        # which is not necessary if otherize is 0
        if self.otherize > 0:
            countkeys = self.counts.keys()
            for countkey in countkeys:
                if self.counts[countkey] < self.otherize:
                    # for a tag whose count is below the threshold, transfer its
                    # count to tag "$other" and delete it
                    self.counts['$other'] += self.counts[countkey]
                    del self.counts[countkey]
                else:
                    # otherwise add it to list of keepers
                    self.keepers.add(countkey)
            
        # now process hashtags again, replacing any tag not in keepers with $other
        self.counts = Counter()
        for savetweet in self.savetweets:
        
            # cleantags gathers unique, lower-cased tags
            cleantags = set()
        
            for hashtag in savetweet:
                t = hashtag['text'].lower()
                if self.otherize == 0 or t in self.keepers:
                    cleantags.add(t)
                else:
                    cleantags.add('$other')
                
            # sort tags and remove tags that are in the exclude set 
            cleantags = sorted(cleantags.difference(self.exclude))
        
            # generate all pairs
            for c in itertools.combinations(cleantags, 2):
                t = c[0] + "," + c[1]
                self.counts[t] += 1
                if self.reciprocal:
                    t = c[1] + "," + c[0]
                    self.counts[t] += 1
        tags = self.counts.keys()
        tags.sort(lambda a, b: cmp(self.counts[b], self.counts[a]))

        return {"profile": profile, "tags": tags, "counts": self.counts}


opt_parser = optparse.OptionParser()
opt_parser.add_option('-e', '--exclude', type=str, default="", 
    help='comma-separated list of hashtags to exclude')
opt_parser.add_option('-o', '--otherize', type=int, default=0, 
    help='threshold below which to treat hashtags as "other"')
opt_parser.add_option('-r', '--reciprocal', action='store_true', default=False, 
    help='add recciprocal links for each pair')
opts, args = opt_parser.parse_args()
# prepare to serialize opts and args as json
# converting opts to str produces string with single quotes,
# but json requires double quotes
optsdict = ast.literal_eval(str(opts))
argsdict = ast.literal_eval(str(args))

otherize = opts.otherize
exclude = set(opts.exclude.lower().split(","))
reciprocal = opts.reciprocal

profiler = CotagsProfiler({
    "otherize": otherize,
    "exclude": exclude,
    "reciprocal": reciprocal})
    
# gather counts for individual tags    
for line in fileinput.input(args):
    try:
        tweet = json.loads(line)
        profiler.process(tweet)
    except ValueError as e:
        sys.stderr.write("uhoh: %s\n" % e)

data = profiler.report()
tags = data["tags"]
counts = data["counts"]

# print csv headers
print "source,target,count"
for tag in counts:
    print (tag + "," + str(counts[tag])).encode('utf8')



