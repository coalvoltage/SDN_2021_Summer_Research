#!/bin/bash

for (( i = 1; i <= $1; i++ ))
do
  ifconfig s"$i"-eth1 10.0.10.$i netmask 255.255.0.0
done
