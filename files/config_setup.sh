#!/bin/bash

CTL=/usr/bin/clearwater-etcdctl

if [[ ! -e $CTL ]]; then
	exit 1
fi

I=0
while :
do
	$CTL ls /clearwater/site1/configuration > /dev/null
	if [[ $? -eq 0 ]]; then
		break
	fi
	sleep 1 

	((I++))
	if [[ $I -gt 10 ]]; then
		exit 1
	fi
done


F=$(mktemp)
$CTL get /clearwater/site1/configuration/shared_config > $F

if [[ -z $(diff -wB $F /etc/clearwater/shared_config) ]]; then
	exit 0
fi
rm $F

# Load config twice (first time always fails?)
/usr/share/clearwater/clearwater-config-manager/scripts/upload_shared_config
/usr/share/clearwater/clearwater-config-manager/scripts/upload_shared_config

