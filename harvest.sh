#!/bin/bash
source venv/bin/activate
export PATH=~/.local/bin:$PATH

PROJECTDIR=$1
if [ -n "$PROJECTDIR" ]; then
SEARCH=`cat projects/$PROJECTDIR/metadata.json | jq -r ".search"`

OUTPUT=projects/$PROJECTDIR/data/tweets/tweets-$(date -d "today" +"%Y%m%d%H%M").json
LASTID=`cat projects/$PROJECTDIR/data/tweets/last-id`
echo Lastid: $LASTID Search: $SEARCH
echo Output to $OUTPUT
twarc --since_id $LASTID search "$SEARCH" > $OUTPUT
NEWLASTID=`cat $OUTPUT | head -1 | jq -r ".id_str"`

if [[ ! -z $NEWLASTID ]]; then
  echo $NEWLASTID > projects/$PROJECTDIR/data/tweets/last-id
fi

echo "Harvested `wc -l $OUTPUT | cut -d " " -f 1` tweets"

# generate html
./generate.sh $PROJECTDIR

else
	echo "Provide project directory name"
fi
