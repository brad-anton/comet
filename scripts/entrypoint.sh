#!/bin/bash
# entrypoint.sh
# @brad_anton
set -e

# Hack just check wait for GCP (TODO: Would be much better not to hardcode this)

PUBSUB_HOSTNAME=gcp-emulator
PUBSUB_PORT=8085
PUBSUB_SCHEMA=http
PUBSUB_HOST=$PUBSUB_SCHEMA://$PUBSUB_HOSTNAME:$PUBSUB_PORT

while [ 1 ]; do
    echo "Checking for $PUBSUB_HOSTNAME:$PUBSUB_PORT"
    ping -c 1 $PUBSUB_HOSTNAME
    RETCODE=`timeout 1 bash -c "</dev/tcp/${PUBSUB_HOSTNAME}/${PUBSUB_PORT}"; echo $?`
    echo "RETCODE: $RETCODE"
    if [ $RETCODE -eq 0 ]; then
        echo "Connection Successful!!"
        break
    fi
    echo "Sleeping"
    sleep 2
done

# Create topic, only needs to run once but if it gets run multiple times,
# its not terrible
#
# basically copy of 
# https://github.com/spotify/comet/blob/master/comet_example/test-tools/pubsub_emulator_setup.sh
curl -H 'Content-Type: application/json' -X PUT  -d '{}' "${PUBSUB_HOST}/v1/projects/${PROJECT_ID}/topics/${PUBSUB_TOPIC}"
curl -H 'Content-Type: application/json' -X PUT  -d "{\"topic\":\"projects/${PROJECT_ID}/topics/${PUBSUB_TOPIC}\"}" "${PUBSUB_HOST}/v1/projects/${PROJECT_ID}/subscriptions/${PUBSUB_SUBSCRIPTION}"

if [ "$1" == 'api' ]; then
    FLASK_APP=comet/api.py flask run

else
    PUBSUB_HOST=$PUBSUB_HOST python -u comet/main.py
fi
