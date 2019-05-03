#!/bin/bash

# Pull the latest version from GIT repository
git pull github master

# Install PIP packages and requirements
pip install -r requirements.txt

# Run the python script
if [ $# -gt 0 ]
then
    python $1
fi