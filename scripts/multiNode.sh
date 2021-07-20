#!/bin/bash
export PATH="$PATH:bin:onos/bin"

ATOMIX_VER=atomix/atomix:3.1.5
ONOS_VER=onosproject/onos

for i in {1..2}
do
  sudo docker container run --detach --name atomix-$i \
	  --hostname atomix-$i $ATOMIX_VER
  sleep 10
  sudo docker inspect atomix-$i | grep -i ipaddress
  sudo docker cp ~/configAuto/atomix-$i.conf atomix-$i:/opt/atomix/conf/atomix.conf
done

for i in {1..2}
do
  sudo docker restart atomix-$i
done

for i in {1..2}
do 
  sudo docker container run -d --name onos-$i --hostname onos-$i \
	 --restart=always $ONOS_VER
  sleep 10
  sudo docker inspect onos-$i | grep -i ipaddress
  sudo docker exec -i onos-$i mkdir /root/onos/config
  sudo docker cp ~/configAuto/cluster-$i.json onos-$i:/root/onos/config/cluster.json
done

for i in {1..2}
do
  sudo docker restart onos-$i
done

OC1=$(sudo docker inspect onos-1 | grep \"IPAddress | cut -d: -f2 | sort -u | tr -d '",')
OC2=$(sudo docker inspect onos-2 | grep \"IPAddress | cut -d: -f2 | sort -u | tr -d '",')

ONOS_INSTANCES="$OC1 $OC2"



OC_COMMAND="app activate org.onosproject.openflow proxyarp layout ; logout"

ssh-keygen -f "/users/jim011/.ssh/known_hosts" -R "[172.17.0.4]:8101"

sleep 5

sshpass -p "karaf" ssh -o StrictHostKeyChecking=no -p 8101 karaf@172.17.0.4 "$OC_COMMAND"
