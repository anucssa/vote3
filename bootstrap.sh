#!/bin/bash

set -euo pipefail

# set up VM
sudo apt-get update
sudo apt-get -y upgrade

sudo apt-get -y install tmux postgresql python3-dev libpq-dev python3-pip python-virtualenv

cd /vagrant

# set up database
cat > /tmp/create_db.sql <<EOF
CREATE USER vote3 WITH PASSWORD 'vote3votingsystempassword';
CREATE DATABASE vote3;
GRANT ALL PRIVILEGES ON DATABASE vote3 TO vote3;
EOF
sudo -u postgres psql -f /tmp/create_db.sql

# set up frontend
cd frontend
# this is broken : https://bugs.launchpad.net/ubuntu/+source/python3.4/+bug/1290847 
# pyvenv-3.4 env
# so we use old virtualenv instead
virtualenv -p /usr/bin/python3.4 env
set +u
source env/bin/activate
set -u
pip install -r requirements.txt
cd vote3fe_project
python manage.py migrate
