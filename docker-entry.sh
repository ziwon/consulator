#!/bin/sh

set +e
curl -sv --fail $CONSUL_URL > /dev/null
ERR=$?
while [ "$ERR" != 0 ]; do
	sleep 5
	echo "trying to connect $CONSUL_URL"
	curl -sv --fail $CONSUL_URL > /dev/null
	ERR=$?
done

#while true; do
#	echo "debugging..."
#	sleep 5
#ßdone

set -e
python3 example/echo.py