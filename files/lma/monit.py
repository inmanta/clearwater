#!/usr/bin/python3

import xmltodict
import requests
import sys
import json

req = requests.get("http://localhost:2812/_status?format=xml", auth=("admin", "monit"))

if req.status_code != 200:
    sys.exit(1)

data = xmltodict.parse(req.text)
up = True
output = []
for svc in data["monit"]["service"]:
    name = svc["name"]
    status = int(svc["status"])
    monitored = int(svc["monitor"])

    output.append({"process": name, "status": status, "monitored": monitored})

print(json.dumps(output))