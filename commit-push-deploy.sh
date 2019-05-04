#!/bin/bash

if [ "$1" != "" ]; then
    git add .
    git commit -m "$1"
    git push github master
fi

# Deploying files on remote host
rsync -rav -e "ssh -p 2222" --exclude='*.git' --exclude='commit-push-deploy.sh' --exclude=env --exclude=.* ./ pi@home.angularize.me:~/Public --progress