import dateutil
import pytz # $ pip install pytz
from collections import Counter
import operator


class Profiler:
    def __init__(self, opts):
        for k, v in opts.items():
            setattr(self, k, v)

        # set defaults
        if not("labelFormat" in opts):
            self.labelFormat = "%Y-%m-%d %H:%M:%S %Z"
        if not("tz" in opts):
            self.tz = pytz.UTC
        if not("extended" in opts):
            self.extended = False
            
        # initialize 
        self.count = 0
        self.retweetcount = 0
        self.geocount = 0
        self.earliest = ""
        self.latest = ""
        self.users = Counter()
        if self.extended:
            self.urls = Counter()
            self.urlcount = 0
        
    def adduser(self, user):
        self.users[user] += 1
        
    def addurl(self, url):
        self.urls[url] += 1
        
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
        self.adduser(user)
        if self.extended:
            if len(tweet["entities"]["urls"]) > 0:
                for url in tweet["entities"]["urls"]:
                    self.addurl(url["expanded_url"])
                self.urlcount += 1
        
    def report(self):
        local_earliest = self.tz.normalize(self.earliest.astimezone(self.tz)).strftime(self.labelFormat)
        local_latest = self.tz.normalize(self.latest.astimezone(self.tz)).strftime(self.labelFormat)
        result = {"count": self.count, 
            "retweetcount": self.retweetcount, 
            "geocount": self.geocount,
            "earliest": local_earliest, 
            "latest": local_latest, 
            "usercount": len(self.users)}
        if self.extended:
            sorted_users = sorted(self.users, key = self.users.get, reverse = True)
            top_users = sorted_users[:10]
            top_users_result = []
            for top_user in top_users:
                top_users_result.append({"name": top_user, "value": self.users[top_user]})
            sorted_urls = sorted(self.urls, key = self.urls.get, reverse = True)
            top_urls = sorted_urls[:10]
            top_urls_result = []
            for top_url in top_urls:
                top_urls_result.append({"name": top_url, "value": self.urls[top_url]})
            result.update({"urlcount": self.urlcount,
                "urls": len(self.urls),
                "topusers": top_users_result,
                "topurls": top_urls_result})
        return result
            
            
class LinkNodesProfiler(Profiler):
    def __init__(self, opts):
        Profiler.__init__(self, opts)
        self.nodes = {}
        self.nodeid = 0

# nodes will end up as 
#  {"userA": 
#    {"id": 27,
#    "source": 0, 
#    "target": 1,
#    "links": {
#        "userB": 3,
#        "userC": 1
#    }
#    
# Meaning that userA mentions userB 3 times, and userB mentions userA once.
# We gather the nodes in a dictionary so that we can look up terms to update 
# counts, but at the end we convert the dictionary into a list sorted by id
# so that the positions in the list correspond to the ids, as D3 requires.

    def addlink(self, source, target):
        if not source in self.nodes:
            self.nodes[source] = {"name": source, "id": self.nodeid, "tweetcount": 0, 
                "source": 1, "target": 0, "links": {}}
            self.nodeid += 1
        else:
            self.nodes[source]["source"] += 1

        if not target in self.nodes:
            targetid = self.nodeid
            self.nodes[target] = {"name": target, "id": self.nodeid, "tweetcount": 0, 
                "source": 0, "target": 1, "links": {}}
            self.nodeid += 1
        else:            
            self.nodes[target]["target"] += 1
            targetid = self.nodes[target]["id"]

        linklist = self.nodes[source]["links"]
        if not target in linklist:
            linklist[target] = {"count": 1, "id": targetid}
        else:
            linklist[target]["count"] += 1
            
    def addsingle(self, name):
        if not name in self.nodes:
            self.nodes[name] = {"name": name, "id": self.nodeid, "tweetcount": 1, 
                "source": 0, "target": 0, "links": {}}
            self.nodeid += 1        

    def report(self):
        profile = Profiler.report(self)
        # convert nodes dictionary to a list, sorted by id
        nodelistkeys = sorted(self.nodes, key=lambda w: self.nodes[w]["id"])
        nodelist = []
        for key in nodelistkeys:
            nodelist.append(self.nodes[key])
        return {"profile": profile, "nodes": nodelist}
            