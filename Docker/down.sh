#!/bin/bash
ThisDir=$(cd $(dirname $0); pwd -P)
if [ "$1" != "" ] && [ -d "$1" ]; then
    shift
    docker compose -f "$ThisDir"/compose.yaml --profile dev-server "$@" down
else
    docker compose -f "$ThisDir"/compose.yaml "$@" down
fi
