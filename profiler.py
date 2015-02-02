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
            self.hashtags = Counter()
            self.hashtagcount = 0
            self.urls = Counter()
            self.urlcount = 0
            self.imageurls = Counter()
            self.imageurlcount = 0
            
        
    def adduser(self, user):
        self.users[user] += 1
        
    def addurl(self, url):
        self.urls[url] += 1
        
    def addhashtag(self, hashtag):
        self.hashtags[hashtag] += 1

    def addimageurl(self, imageurl):
        self.imageurls[imageurl] += 1

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
            # handle urls
            if len(tweet["entities"]["urls"]) > 0:
                for url in tweet["entities"]["urls"]:
                    self.addurl(url["expanded_url"])
                self.urlcount += 1
                
            # handle hashtags
            if len(tweet["entities"]["hashtags"]) > 0:
                for tag in tweet['entities']['hashtags']:
                    # hashtags are not case sensitive, so lower() to dedupe
                    # or just leave it and accept dupes?
                    self.addhashtag(tag['text'].lower())
                self.hashtagcount += 1
            
            # handle imageurls
            if 'media' in tweet['entities']:
                hasimageurl = False
                for media in tweet['entities']['media']:
                    if media['type'] == 'photo':
                        self.addimageurl(media['media_url'])
                        hasimageurl = True
                if hasimageurl:
                    self.imageurlcount += 1

        
    def tops(self, list, title):
        # given a list of name-value pairs, return the top 10 pairs by value,
        # and a list of integers representing the percent of total value
        # held by each of 10 slices
        
        totalcount = len(list)
        totalvalue = int(sum(list.values()))
        sorted = list.most_common()
        
        top = sorted[:10]
        top_result = []
        for name, value in top:
            top_result.append({"name": name, "value": value})

        step = float(totalcount) / 10
        percentiles = []
        for i in range(0, 10):
            start = int(i * step)
            end = int((i + 1) * step)
            slicecount = end - start
            # weight the slice value as if the slice were an even 10th of the list
            weight = 10 / (float(slicecount) / totalcount)
            slicevalue = sum(v for k,v in sorted[start:end])
            percentile = int(round(float(slicevalue) / totalvalue * weight))
            percentiles.append(percentile)
        return {"top" + title: top_result, title+"percentiles": percentiles}
    
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
            result.update(self.tops(self.users, "users"))
            result.update(self.tops(self.hashtags, "hashtags"))
            result.update(self.tops(self.urls, "urls"))
            result.update(self.tops(self.imageurls, "imageurls"))
            result.update({"urlcount": self.urlcount, "urls": len(self.urls), 
                "imageurlcount": self.imageurlcount, "imageurls": len(self.imageurls),
                "hashtagcount": self.hashtagcount, "hashtags": len(self.hashtags)})
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
            