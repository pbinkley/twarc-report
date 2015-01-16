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