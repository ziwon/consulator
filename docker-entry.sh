#!/bin/sh

export HOST=${HOST:-"localhost"}
export PORT=${PORT:-"8000"}
export BIND_INTERFACE=${BIND_INTERFACE:-"eth0"}

set +e
curl -sv --fail $CONSUL_URL > /dev/null
ERR=$?
while [ "$ERR" != 0 ]; do
	sleep 5
	echo "trying to connect $CONSUL_URL"
	eval "curl -sv --fail $CONSUL_URL" > /dev/null
	ERR=$?
done

set -e
python3 example/echo.py