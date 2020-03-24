#!/bin/bash

PROJECTDIR=$1
DATE=`date "+%Y-%m-%dT%H:%M:%S"`

cd projects/$PROJECTDIR/html
git add .
git commit -m "$DATE update"
git push
print "Pushed commit: $DATE"
