#!/usr/local/bin/bash

CONFIG_FILE=/my/folder/config.yaml

TEAMS=$(cat ${CONFIG_FILE} |shyaml get-values teams |grep "name:" |cut -f2 -d":")

for TEAM in ${TEAMS}
do
  echo "Generating AWS cost report for team ${TEAM}"
  docker -H :4000 run -d -v ${CONFIG_FILE}:/config.yaml signiant/aws-team-cost-reporter -c /config.yaml -t ${TEAM}
done
