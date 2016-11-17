#!/bin/bash

hostname {{ name }}

apt-get update
apt-get install -y python3 python3-pip git python-virtualenv

virtualenv -p python3 /opt/inmanta
/opt/inmanta/bin/pip3 install -U pip
/opt/inmanta/bin/pip3 install -U setuptools
/opt/inmanta/bin/pip3 install inmanta

mkdir -p /etc/inmanta
cat > /etc/inmanta/agent.cfg <<EOF
[config]
heartbeat-interval = 60
fact-expire = 60
state-dir=/var/lib/inmanta

environment={{ env_id }}
agent-names=\$node-name

[agent_rest_transport]
port={{port}}
host={{env_server}}
EOF

cat > /etc/init/inmanta.conf <<EOF
# inmanta - Inmanta cfg mgmt agent
#
# Inmanta agent
description "Inmanta"

start on runlevel [2345]
stop on runlevel [!2345]

expect fork
respawn

exec /opt/inmanta/bin/inmanta -c /etc/inmanta/agent.cfg -vvv agent
EOF

initctl reload-configuration
start inmanta
