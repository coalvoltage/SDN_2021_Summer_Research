#!/bin/bash

sudo ovs-vsctl add-br br0
sudo ovs-vsctl add-br br1
sudo ovs-vsctl add-br br2


sudo ovs-vsctl add-port br0 s1_gre0 -- set interface s1_gre0 type=gre options:remote_ip=10.0.10.2
sudo ovs-vsctl add-port br0 s2_gre0 -- set interface s2_gre0 type=gre options:remote_ip=10.0.10.1
sudo ovs-vsctl add-port br1 s2_gre1 -- set interface s2_gre1 type=gre options:remote_ip=10.0.10.3
sudo ovs-vsctl add-port br1 s3_gre0 -- set interface s3_gre0 type=gre options:remote_ip=10.0.10.2
sudo ovs-vsctl add-port br2 s3_gre0 -- set interface s4_gre1 type=gre options:remote_ip=10.0.10.4
sudo ovs-vsctl add-port br2 s4_gre0 -- set interface s3_gre0 type=gre options:remote_ip=10.0.10.3

sudo ovs-vsctl set interface s1_gre0 bfd:min_rx=3 -- set interface s1_gre0 bfd:min_tx=1
sudo ovs-vsctl set interface s1_gre0 bfd:bfd_src_ip=10.0.10.1 -- set interface s1_gre0 bfd:bfd_dst_ip=10.0.10.2
sudo ovs-vsctl set interface s1_gre0 bfd:enable=true

sudo ovs-vsctl set interface s2_gre0 bfd:min_rx=3 -- set interface s2_gre0 bfd:min_tx=1
sudo ovs-vsctl set interface s2_gre0 bfd:bfd_src_ip=10.0.10.2 -- set interface s2_gre0  bfd:bfd_dst_ip=10.0.10.1
sudo ovs-vsctl set interface s2_gre0 bfd:enable=true

sudo ovs-vsctl set interface s2_gre1 bfd:min_rx=3 -- set interface s2_gre1 bfd:min_tx=1
sudo ovs-vsctl set interface s2_gre1 bfd:bfd_src_ip=10.0.10.2 -- set interface s2_gre1 bfd:bfd_dst_ip=10.0.10.3
sudo ovs-vsctl set interface s2_gre1 bfd:enable=true


sudo ovs-vsctl set interface s3_gre0 bfd:min_rx=3 -- set interface s3_gre0 bfd:min_tx=1
sudo ovs-vsctl set interface s3_gre0 bfd:bfd_src_ip=10.0.10.3 -- set interface s3_gre0 bfd:bfd_dst_ip=10.0.10.2
sudo ovs-vsctl set interface s3_gre0 bfd:enable=true

sudo ovs-vsctl set interface s3_gre1 bfd:min_rx=3 -- set interface s3_gre1 bfd:min_tx=1
sudo ovs-vsctl set interface s3_gre1 bfd:bfd_src_ip=10.0.10.3 -- set interface s3_gre1 bfd:bfd_dst_ip=10.0.10.4
sudo ovs-vsctl set interface s3_gre1 bfd:enable=true

sudo ovs-vsctl set interface s4_gre0 bfd:min_rx=3 -- set interface s4_gre0 bfd:min_tx=1
sudo ovs-vsctl set interface s4_gre0 bfd:bfd_src_ip=10.0.10.4 -- set interface s4_gre0 bfd:bfd_dst_ip=10.0.10.3
sudo ovs-vsctl set interface s4_gre0 bfd:enable=true

