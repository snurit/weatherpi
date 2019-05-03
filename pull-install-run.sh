#!/bin/bash

# Activate env
source /env/bin/activate

# Pull the latest version from GIT repository
git pull github master

# Install PIP packages and requirements
pip install -r requirements.txt

# Run the python script
if [ "$1" != "" ]; then
    python $1
fi