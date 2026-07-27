#!/bin/sh
if which -s mosquitto_sub && which -s jq; then
    mosquitto_sub -h `docker inspect mqtt_broker  |jq '.[0]["NetworkSettings"]["Networks"]["docker_default"]["IPAddress"]' | sed -e 's/"//g'` -p 1883 -t '#' -F '%t'
else
    echo mosquitto_sub and jq are required 1>&2
fi
