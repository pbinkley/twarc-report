#!/bin/bash
source venv3/bin/activate

PROJECTDIR=$1

# generate html
twarc/utils/wordcloud.py projects/$PROJECTDIR/data/tweets/*.json > projects/$PROJECTDIR/html/wordcloud.html
twarc/utils/sort_by_id.py projects/$PROJECTDIR/data/tweets/*.json > projects/$PROJECTDIR/data/amalgamated.json
#twarc/utils/network.py --users projects/$PROJECTDIR/data/amalgamated.json projects/$PROJECTDIR/html/network-users.html
#twarc/utils/network.py projects/$PROJECTDIR/data/amalgamated.json projects/$PROJECTDIR/html/network.html
#twarc/utils/wall.py projects/$PROJECTDIR/data/amalgamated.json > projects/$PROJECTDIR/wall.html
./d3cotags.py -e $PROJECTDIR projects/$PROJECTDIR > projects/$PROJECTDIR/html/cotags.html
./d3graph.py --mode mentions projects/$PROJECTDIR > projects/$PROJECTDIR/html/mentionsgraph.html
./d3graph.py --mode retweets projects/$PROJECTDIR > projects/$PROJECTDIR/html/retweetsgraph.html
./d3graph.py --mode replies projects/$PROJECTDIR > projects/$PROJECTDIR/html/repliesgraph.html
./d3times.py -a -t "America/Edmonton" -i 3H projects/$PROJECTDIR > projects/$PROJECTDIR/html/timebargraph.html
./reportprofile.py -o html projects/$PROJECTDIR/data/amalgamated.json  > projects/$PROJECTDIR/html/index.html 
./reportprofile.py projects/$PROJECTDIR
twarc dehydrate projects/$PROJECTDIR/data/amalgamated.json > projects/$PROJECTDIR/html/tweet-ids.txt
