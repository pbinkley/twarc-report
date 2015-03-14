#!/usr/bin/env python

import optparse
import re
import dateutil.parser
from profiler import TimeProfiler
import pytz
import d3output

opt_parser = optparse.OptionParser()
opt_parser.add_option("-t", "--timezone", type=str, default="", 
    help="output timezone (e.g. 'America/New_York' or 'local'; default: UTC)")
opt_parser.add_option("-w", "--maxwords", dest="maxwords", type="int", 
    help="maximum number of words to display (default: 25)", default=25)
opt_parser.add_option("-i", "--interval", dest="intervalStr", type="str", 
    help="interval for grouping timestamps, in seconds, minutes or hours, e.g. 15M (default: 1H)", 
    default="1H")
opt_parser.add_option("-s", "--start", type=str, default=None, 
    help="start date/time")
opt_parser.add_option("-e", "--end", type=str, default=None, 
    help="end date/time")
opt_parser.add_option("-o", "--output", dest="output", type="str", 
    help="html | csv | json (default: html)", default="html")
opt_parser.add_option("-p", "--template", dest="template", type="str", 
    help="name of template in utils/template (default: wordcloud.html)", default="wordcloud.html")

opts, args = opt_parser.parse_args()

tzname = opts.timezone
# determine output time zone
if tzname == "":
    tz = pytz.UTC
elif tzname == "local":
    tz = get_localzone() # system timezone, from tzlocal
else: 
    tz = pytz.timezone(tzname)

maxwords = opts.maxwords
intervalStr = opts.intervalStr
output = opts.output

start = opts.start
end = opts.end
if opts.start:
    start = tz.localize(dateutil.parser.parse(start + "0001-01-01 00:00:00"[len(start):]))
if opts.end:
    end = tz.localize(dateutil.parser.parse(end + "9999-12-31 23:11:59"[len(end):]))

# from https://gist.github.com/uogbuji/705383
GRUBER_URLINTEXT_PAT = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')

class WordcloudTimeProfiler(TimeProfiler):
    def __init__(self, opts):
        TimeProfiler.__init__(self, opts)
        self.timeslices = {}
        self.stop_words = set(line.strip().lower() for line in open("stopwords/stop-words_english_6_en.txt"))

    def process(self, tweet):
        created_at = dateutil.parser.parse(tweet["created_at"])
        if ((self.start is None) or (created_at >= self.start)) and ((self.end is None) 
                or (created_at <= self.end)):
            timeslice = TimeProfiler.process(self, tweet)
            if not timeslice in self.timeslices:
                self.timeslices[timeslice] = {}
            word_counts = self.timeslices[timeslice]
            text = tweet["text"]
            # remove hashtags and user names
            text = re.sub("(^|[^\w])[@#]\w*", "\g<1>", text)
            # remove urls
            text = re.sub(GRUBER_URLINTEXT_PAT, " ", text)
            # trim punctuation next to space
            text = re.sub(ur"[^\w\s]+(\s|$)|(^|\s)[^\w\s]+", " ", text, re.UNICODE)
            # replace internal punctuation, except apostrophes
            text = re.sub(ur"[^\w\s\']", " ", text, re.UNICODE)
            for word in text.split():
                word = word.lower()
                if len(word) < 3: continue
                if len(word) > 15: continue
                if word in self.stop_words: continue
                if word.startswith("rt"): continue
                if not re.match("^[a-z]", word, re.IGNORECASE): continue
                # remove final 's
                word = re.sub("\'s$", "", word)
                if len(word) > 0:
                    word_counts[word] = word_counts.get(word, 0) + 1

    def report(self):
        data = TimeProfiler.report(self)
        data["profile"]["start"] = str(self.start)
        data["profile"]["end"] = str(self.end)
        for value in data["values"]:
            thisslice = self.timeslices[value["name"]]
            # sort words by value
            sorted_words = thisslice.keys()
            sorted_words.sort(lambda a, b: cmp(thisslice[b], thisslice[a]))
            top_words = sorted_words[0:maxwords]
            words = []
            for word in top_words:
                words.append({
                    "text": word,
                    "count": thisslice[word]
                })
            value["words"] = words
        return data

profiler = WordcloudTimeProfiler({
    "tz": tz, 
    "output": "json", 
    "aggregate": True, 
    "intervalStr": intervalStr,
    "start": start,
    "end": end})

profiler.gettweets(opts, args)

data = profiler.report()

if opts.output == "embed":
    d3output.embed(opts.template, data)
else:
    print data
