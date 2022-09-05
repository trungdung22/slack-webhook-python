#!/bin/bash

set -e

echo "Comsumer starting..." &
exec python3 main.py "slack.observed"