#!/bin/bash

gpg --keyserver hkp://keys.gnupg.net --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3
sudo apt-get install build-essential git --yes
curl -L https://get.rvm.io | bash -s stable
source ~/.rvm/scripts/rvm
rvm autolibs enable
rvm install 1.9.3
rvm use 1.9.3

git clone -b stable --recursive git@github.com:Metaswitch/clearwater-live-test.git
cd clearwater-live-test
bundle install
