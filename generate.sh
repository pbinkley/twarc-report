#!/bin/bash
source venv/bin/activate

PROJECTDIR=$1

# generate html
twarc/utils/wordcloud.py projects/$PROJECTDIR/data/tweets/*.json > projects/$PROJECTDIR/wordcloud.html
twarc/utils/sort_by_id.py projects/$PROJECTDIR/data/tweets/*.json > projects/$PROJECTDIR/data/amalgamated.json
twarc/utils/network.py --users projects/$PROJECTDIR/data/amalgamated.json projects/$PROJECTDIR/network-users.html
twarc/utils/network.py projects/$PROJECTDIR/data/amalgamated.json projects/$PROJECTDIR/network.html
#twarc/utils/wall.py projects/$PROJECTDIR/data/amalgamated.json > projects/$PROJECTDIR/wall.html
./d3cotags.py -e $PROJECTDIR projects/$PROJECTDIR > projects/$PROJECTDIR/cotags.html
./d3graph.py --mode mentions projects/$PROJECTDIR > projects/$PROJECTDIR/mentionsgraph.html
./d3graph.py --mode retweets projects/$PROJECTDIR > projects/$PROJECTDIR/retweetsgraph.html
./d3graph.py --mode replies projects/$PROJECTDIR > projects/$PROJECTDIR/repliesgraph.html
./d3times.py -a -t "America/Edmonton" -i 5M projects/$PROJECTDIR > projects/$PROJECTDIR/timebargraph.html
./reportprofile.py projects/$PROJECTDIR
twarc dehydrate projects/$PROJECTDIR/data/amalgamated.json > projects/$PROJECTDIR/data/tweet-ids.txt