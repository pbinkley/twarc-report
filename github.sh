#!/bin/bash

source ./github-credentials

PROJECTDIR=$1
source ./projects/$PROJECTDIR/github-repo

DATE=`date "+%Y-%m-%dT%H-%M-%S"`

cd projects/$PROJECTDIR/html
git add .
git commit -m "$DATE update"
git push https://$GITHUB_TOKEN@github.com/pbinkley/$GITHUB_REPO.git
echo "Pushed commit: $DATE"
