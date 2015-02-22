import dateutil
import dateutil.parser # $ pip install python-dateutil
import datetime
import pytz # $ pip install pytz
from collections import Counter
import operator
import re
import d3output

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
        if not("blocks" in opts):
            self.blocks = ["all"]
        if "all" in self.blocks:
            self.blocks.extend(["topusers", "tophashtags", "topurls", "topimageurls", "urls", 
                "imageurls"])
            
        # initialize 
        self.count = 0
        self.retweetcount = 0
        self.geocount = 0
        self.earliest = ""
        self.latest = ""
        self.users = Counter()
        if self.extended:
            if "tophashtags" in self.blocks: 
                self.hashtags = Counter()
                self.hashtagcount = 0
            if "urls" in self.blocks or "topurls" in self.blocks:
                self.urls = Counter()
                self.urlcount = 0
            if "imageurls" in self.blocks or "topimageurls" in self.blocks:
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
            if "urls" in self.blocks or "topurls" in self.blocks:
                if len(tweet["entities"]["urls"]) > 0:
                    for url in tweet["entities"]["urls"]:
                        self.addurl(url["expanded_url"])
                    self.urlcount += 1
                
            # handle hashtags
            if "hashtags" in self.blocks or "tophashtags" in self.blocks:
                if len(tweet["entities"]["hashtags"]) > 0:
                    for tag in tweet['entities']['hashtags']:
                        # hashtags are not case sensitive, so lower() to dedupe
                        # or just leave it and accept dupes?
                        self.addhashtag(tag['text'].lower())
                    self.hashtagcount += 1
            
            # handle imageurls
            if "imageurls" in self.blocks or "topimageurls" in self.blocks:
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
            if "topusers" in self.blocks:
                result.update(self.tops(self.users, "users"))
            if "tophashtags" in self.blocks:
                result.update(self.tops(self.hashtags, "hashtags"))
            if "topurls" in self.blocks:
                result.update(self.tops(self.urls, "urls"))
            if "urls" in self.blocks:
                result.update({"urlcount": self.urlcount, "urls": len(self.urls), 
                    "imageurlcount": self.imageurlcount, "imageurls": len(self.imageurls),
                    "hashtagcount": self.hashtagcount, "hashtags": len(self.hashtags)})
            if "topimageurls" in self.blocks:
                result.update(self.tops(self.imageurls, "imageurls"))
            if "imageurls" in self.blocks:
                result.update({"imageurlslist": self.imageurls})
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

class TimeProfiler(Profiler):
    # interval, in milliseconds
    intervalFormats = {
        "S": {"name": "second", "format": "%Y-%m-%d %H:%M:%S", "interval": 1000},
        "M": {"name": "minute", "format": "%Y-%m-%d %H:%M", "interval":  1000 * 60},
        "H": {"name": "hour", "format": "%Y-%m-%d %H", "interval":  1000 * 60 * 60},
        "d": {"name": "day", "format": "%Y-%m-%d", "interval":  1000 * 60 * 60 * 24},
        "m": {"name": "month", "format": "%Y-%m", "interval":  1000 * 60 * 60 * 24 * 28},
        "Y": {"name": "year", "format": "%Y-%m", "interval":  1000 * 60 * 60 * 24 * 365}
    }
    def __init__(self, opts):
        Profiler.__init__(self, opts)
        try:
            self.intervalParts = re.search("([0-9]*)([^0-9]*)", self.intervalStr)
            if self.intervalParts.group(1) == "":
                self.intervalCount = 1
            else:
                self.intervalCount = int(self.intervalParts.group(1))
            self.intervalUnit = self.intervalParts.group(2)
            self.interval = self.intervalCount * self.intervalFormats[self.intervalUnit]["interval"]
            self.format = self.intervalFormats[self.intervalUnit]["format"]
            self.intervalLabel = str(self.intervalCount) + " " + self.intervalFormats[self.intervalUnit]["name"]
            if self.intervalCount > 1:
                self.intervalLabel += "s"

        except ValueError as e:
            sys.stderr.write("uhoh: %s\n" % e)

        # gather in a dict with count if aggregating, otherwise in a list
        if self.aggregate:
            self.items = {}
        else:
            self.items = []

    def process(self, tweet):
        Profiler.process(self, tweet)
        created_at = dateutil.parser.parse(tweet["created_at"])
        local_dt = self.tz.normalize(created_at.astimezone(self.tz))
        if self.intervalStr != '':
            if self.intervalUnit == "S":
                local_dt = local_dt - datetime.timedelta(seconds=local_dt.second % int(self.intervalCount))
            elif self.intervalUnit == "M":
                local_dt = local_dt - datetime.timedelta(minutes=local_dt.minute % int(self.intervalCount))
            elif self.intervalUnit == "H":
                local_dt = local_dt - datetime.timedelta(hours=local_dt.hour % int(self.intervalCount))
        # otherwise use format to aggregate values - though this treats intervalCount as 1
        result = local_dt.strftime(self.format)
        if self.aggregate:
            self.items[result] = self.items.get(result, 0) + 1
        else:
            self.items.append(result)
        # return the time slice label
        return result
            
    def report(self):
        profile = Profiler.report(self)
        if self.output == "csv":
            if self.aggregate:
                values = d3output.namevaluecsv(self.items)
            else:
                values = d3output.valuecsv(self.items)
            return values
        else:
            if self.aggregate:
                values = d3output.namevaluejson(self.items)
            else:
                values = d3output.valuejson(self.items)
            return {"profile": profile, "values": values}
