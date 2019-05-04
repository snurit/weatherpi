#!/bin/bash

# Pull the latest version from GIT repository
git pull github master

# Run $1 app with -e option $2
python $1 -e $2