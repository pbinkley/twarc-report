#!/usr/bin/env python

import os
import sys
import json
import csv
import StringIO

def nodeslinks(threshold):

    nodes = []
    links = []
    
    # lines look like "nodeA,nodeB,123"
    for line in sys.stdin:
        tokens = line.split(",")
        # use try to ignore header line
        try:
            if int(tokens[2]) >= threshold:
                if not tokens[0] in nodes:
                    nodes.append(tokens[0])
                if not tokens[1] in nodes:
                    nodes.append(tokens[1])
                links.append({"source": nodes.index(tokens[0]), 
                "target": nodes.index(tokens[1]), 
                "value": int(tokens[2])}) 
        except:
            continue
    
    nodelist = []
    for node in nodes:
        nodelist.append({"name": node})
    
    print json.dump({"nodes": nodelist, "links": links})

def nodeslinktrees(profile, nodes, opts, args):
    # generate nodes json
    nodesoutput = []
    linksoutput = []
    graph = opts["graph"]
    for node in nodes:
        if graph == "directed":
            title = " (" + str(node["tweetcount"]) + " tweet"
            if node["tweetcount"] != 1:
                title += "s"
            title += ": " + str(node["source"]) + " out/" + str(node["target"]) + " in)"
        else:
            title = " (" + str(node["tweetcount"]) + " tweet"
            if node["tweetcount"] != 1:
                title += "s"
            title += ")"
        nodesoutput.append({"name": node["name"], 
            "title": str(node["name"]) + title})
       
        # generate links
        for targetname in node["links"].iterkeys():
            target = node["links"][targetname]
            if target["count"] >= opts["threshold"]:
                linksoutput.append({
                    "source": node["id"], 
                    "target": target["id"], 
                    "value": target["count"]
                })

    return {"profile": profile, "nodes": nodesoutput, "links": linksoutput, "opts": opts, "args": args}

def namevaluecsv(data):
    csvout = StringIO.StringIO()
    csvwriter = csv.writer(csvout)
    csvwriter.writerow(["name", "value"])
    for key, value in sorted(data.iteritems()):
        csvwriter.writerow([key, value])
    return csvout.getvalue()
    
def valuecsv(data):
    csvout = StringIO.StringIO()
    csvwriter = csv.writer(csvout)
    csvwriter.writerow(["value"])
    for d in data:
        csvwriter.writerow([d])
    return csvout.getvalue()
    
def nodeslinkcsv(data):
    # convert link-nodes objects into csv
    # e.g. {"A": {"B": 3, "C": 7}} to A,B,3 and A,C,7
    csvout = StringIO.StringIO()
    csvwriter = csv.writer(csvout)
    csvwriter.writerow(["source", "target", "value"])
    for node in data:
        source = node["name"]
        # generate csv rows
        for targetname in node["links"].iterkeys():
            csvwriter.writerow([source, targetname, node["links"][targetname]["count"]])
    return csvout.getvalue()

def namevaluejson(data):
    output = []
    for key, value in sorted(data.iteritems()):
        output.append({"name": key, "value": value})
    return output
    
def valuejson(data):
    output = []
    for d in data:
        output.append(d)
    return output

def embed(template, d3json):
    # generate html by replacing token
    template_file = os.path.join(os.path.dirname(__file__), "templates", template)
    with open (template_file, "r") as template:
        print template.read().replace('$JSON$', json.dumps(d3json))
