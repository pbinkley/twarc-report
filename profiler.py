import dateutil
import pytz # $ pip install pytz
from collections import Counter


class Profiler:
    def __init__(self, opts):
        for k, v in opts.items():
            setattr(self, k, v)

        # set defaults
        if not("labelFormat" in opts):
            self.labelFormat = "%Y-%m-%d %H:%M:%S %Z"
        if not("tz" in opts):
            self.tz = pytz.UTC
            
        # initialize 
        self.count = 0
        self.retweetcount = 0
        self.geocount = 0
        self.earliest = ""
        self.latest = ""
        self.users = Counter()
        
    def process(self, tweet):
        self.count += 1
        if "retweeted_status" in tweet:
            self.retweetcount += 1
        if tweet.get("geo") != None:
            self.geocount += 1
        self.created_at = dateutil.parser.parse(tweet["created_at"])
        if self.earliest == "" or self.earliest > self.created_at:
            self.earliest = self.created_at
        if self.latest == "" or self.latest < self.created_at:
            self.latest = self.created_at
        user = tweet["user"]["screen_name"]
        self.users[user] += 1

        
    def report(self):
        local_earliest = self.tz.normalize(self.earliest.astimezone(self.tz)).strftime(self.labelFormat)
        local_latest = self.tz.normalize(self.latest.astimezone(self.tz)).strftime(self.labelFormat)
        return {"count": self.count, 
            "retweetcount": self.retweetcount, 
            "geocount": self.geocount,
            "earliest": local_earliest, 
            "latest": local_latest, 
            "usercount": len(self.users)}
            
            
class LinkNodesProfiler(Profiler):
    def __init__(self, opts):
        Profiler.__init__(self, opts)
        self.links = {}
        self.nodes = {}
# nodes will end up as ["userA", "userB", ...]
# links will end up as 
#    {
#        "userA": {"userB": 3, ...},
#        "userB": {"userA": 1, ...},
#        ...
#    }
#    
# Meaning that userA mentions userB 3 times, and userB mentions userA once.

    def addlink(self, source, target):
        if not source in self.links:
            self.links[source] = {}
            
        if not source in self.nodes:
            self.nodes[source] = {"source": 0, "target": 1}
        else:
            self.nodes[source]["target"] += 1

        linklist = self.links[source]
        if target in linklist:
            linklist[target] += 1
        else:
            linklist[target] = 1

        if target in self.nodes:
            self.nodes[target]["source"] += 1
        else:
            self.nodes[target] = {"source": 1, "target": 0}

    def report(self):
        profile = Profiler.report(self)
        return {"profile": profile, "nodes": self.nodes, "links": self.links}
            