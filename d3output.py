#!/usr/bin/env python

import os
import sys
import json
import csv
import io

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
    
    print(json.dump({"nodes": nodelist, "links": links}))

def nodeslinktrees(profile, nodes):
    # generate nodes json
    nodesoutput = []
    linksoutput = []
    if hasattr(profile["opts"], "graph"):
        graph = profile["opts"]["graph"]
    else:
        graph = ""
    for node in nodes:
        if graph == "directed":
            title = " (" + str(node["tweetcount"]) + " tweet"
            if node["tweetcount"] != 1:
                title += "s"
            title += ": " + unicode(node["source"]) + " out/" + unicode(node["target"]) + " in)"
        else:
            title = " (" + str(node["tweetcount"]) + " tweet"
            if node["tweetcount"] != 1:
                title += "s"
            title += ")"
        nodesoutput.append({"name": node["name"], 
            "title": node["name"] + title})
       
        # generate links
        for targetname in node["links"].keys():
            target = node["links"][targetname]
            if target["count"] >= profile["opts"]["threshold"]:
                linksoutput.append({
                    "source": node["id"], 
                    "target": target["id"], 
                    "value": target["count"]
                })

    return {"profile": profile, "nodes": nodesoutput, "links": linksoutput}

def namevaluecsv(data):
    csvout = io.StringIO()
    csvwriter = csv.writer(csvout)
    csvwriter.writerow(["name", "value"])
    for key, value in sorted(data.items()):
        csvwriter.writerow([key, value])
    return csvout.getvalue()
    
def valuecsv(data):
    csvout = io.StringIO()
    csvwriter = csv.writer(csvout)
    csvwriter.writerow(["value"])
    for d in data:
        csvwriter.writerow([d])
    return csvout.getvalue()
    
def nodeslinkcsv(data):
    # convert link-nodes objects into csv
    # e.g. {"A": {"B": 3, "C": 7}} to A,B,3 and A,C,7
    csvout = io.StringIO()
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
    for key, value in sorted(data.items()):
        output.append({"name": key, "value": value})
    return output
    
def valuejson(data):
    output = []
    for d in data:
        output.append(d)
    return output

def embed(template, d3json):
    # load metadata.json if present
    # d3json["args"] contains filenams passed in, with wildcards resolved
    if d3json["profile"]["metadatafile"]:
        metadata_file = d3json["profile"]["metadatafile"]
    else:
        metadata_file = os.path.join(os.path.dirname(d3json["profile"]["args"][0]), "metadata.json")
    try:
        with open(metadata_file) as json_data:
            metadata = json.load(json_data)
            json_data.close()
    except:
        #sys.exit("Cannot read metadata file " + metadata_file)
        metadata = {"title": d3json["profile"]["args"][0] 
                    + (" (+)" if len(d3json["profile"]["args"]) > 1 else "") }
    d3json["metadata"] = metadata
    # generate html by replacing token in template
    template_file = os.path.join(os.path.dirname(__file__), "templates", template)
    with open (template_file, "r") as template:
        output = template.read()
        output = output.replace("$TITLE$", metadata["title"])
        output = output.replace("$DATA$", json.dumps(d3json))
        print(output)
