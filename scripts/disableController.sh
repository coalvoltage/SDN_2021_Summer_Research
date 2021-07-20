#!/bin/bash

now="$(date +'%H.%M.%S.%N')"

echo "$now"

sudo docker stop $1
