#!/bin/bash

# Activate env
source ./env/bin/activate

# Pull the latest version from GIT repository
git pull github master

# Install PIP packages and requirements
pip install -r requirements_dist.txt