#!/usr/bin/env python

import json
import itertools
import optparse
import d3output # local module
from profiler import Profiler # local module
from profiler import LinkNodesProfiler # local module
from collections import Counter

class CotagsProfiler(LinkNodesProfiler):
    def __init__(self, opts):
        LinkNodesProfiler.__init__(self, opts)
        self.savetweets = []
        self.counts = Counter()
        self.keepers = set()

    def process(self, tweet):
        Profiler.process(self, tweet)
        # gather a list of the tags in this tweet, lowercased
        savetweet = []
        for tag in tweet["entities"]["hashtags"]:
            t = tag["text"].lower()
            savetweet.append(t)
            # and increment count for this tag
            self.counts[t] += 1
        # add tag list to savetweets
        self.savetweets.append(savetweet)

    def report(self):
        # for tags below the threshold, replace with "-OTHER"
        # which is not necessary if threshold is 0
        if self.threshold > 0:
            countkeys = self.counts.keys()
            for countkey in countkeys:
                if self.counts[countkey] < self.threshold:
                    # for a tag whose count is below the threshold, transfer its
                    # count to tag "-OTHER" and delete it
                    if self.keepother:
                        self.counts["-OTHER"] += self.counts[countkey]
                    del self.counts[countkey]
                else:
                    # otherwise add it to list of keepers
                    self.keepers.add(countkey)
            if self.keepother:
                self.keepers.add("-OTHER")
            # keepers now has a complete set of surviving tags

        # now process hashtags in tweets again, replacing any tag not in keepers with -OTHER
        self.counts = Counter()
        for savetweet in self.savetweets:
        
            # cleantags gathers unique, lower-cased tags for this tweet
            cleantags = set()
        
            for tag in savetweet:
                if self.threshold == 0 or tag in self.keepers:
                    cleantags.add(tag)
                else:
                    if self.keepother:
                        cleantags.add("-OTHER")
                
            # sort tags and remove tags that are in the exclude set 
            cleantags = sorted(cleantags.difference(self.exclude))
            
            # generate all pairs
            for c in itertools.combinations(cleantags, 2):
                self.addlink(c[0], c[1])
                if self.reciprocal:
                    self.addlink(c[1], c[0])
            
            # if this tag is the only one we're including from this tweet,
            # then there won't be any combinations, and so it won't have
            # been added to self.nodes by addlink: so add it.

            # add to tweet count for this tag
            for tag in cleantags:
                if tag in self.nodes:
                    self.nodes[tag]["tweetcount"] += 1
                else:
                    self.addsingle(tag)
                
        data = LinkNodesProfiler.report(self)
        return data;        
            

opt_parser = optparse.OptionParser()
opt_parser.add_option("-o", "--output", dest="output", type="str", 
    help="html | json (default: html)", default="html")
opt_parser.add_option("-e", "--exclude", type=str, default="", 
    help="comma-separated list of hashtags to exclude")
opt_parser.add_option("-t", "--threshold", type=int, default=0, 
    help="threshold below which to treat hashtags as 'other'")
opt_parser.add_option("-r", "--reciprocal", action="store_true", default=False, 
    help="add reciprocal links for each pair")
opt_parser.add_option("-p", "--template", dest="template", type="str", 
    help="name of template in utils/template (default: graph.html)", default="graph.html")
opt_parser.add_option("-k", "--keepother", action="store_true", default=False, 
    help="include -OTHER tag in output for tags below threshold")

opts, args = opt_parser.parse_args()

threshold = opts.threshold
exclude = set(opts.exclude.lower().split(","))
reciprocal = opts.reciprocal
keepother = opts.keepother
output = opts.output

profiler = CotagsProfiler({
    "threshold": threshold,
    "exclude": exclude,
    "reciprocal": reciprocal,
    "keepother": keepother,
    "graph": "undirected",
    "field": "hashtag"})
    
profiler.gettweets(opts, args)

data = profiler.report()

profile = data["profile"]
nodes = data["nodes"]

if output == "csv":
    print d3output.nodeslinkcsv(nodes)
elif output == "json":
    values = d3output.nodeslinktrees(profile, nodes)
    print {"profile": profile, "values": values}
elif output == "html":
    print d3output.embed(opts.template, d3output.nodeslinktrees(profile, nodes))


