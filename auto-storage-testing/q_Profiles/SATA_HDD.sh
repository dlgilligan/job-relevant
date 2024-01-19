#!/bin/bash

#use lsblk to get the MAJ:MIN of the RAID drive then put the number in DEVICE, D and Q
#or use lsblk to get the name of the RAID drive (such as sdb) and run the script using "sh SATA_SSD.sh sdb"


DEVICE=$1

D=/sys/block/$1/device
Q=/sys/block/$1/queue


echo 64 > $D/queue_depth
echo 1024 > $Q/nr_requests
echo mq-deadline > $Q/scheduler

#for max_sectors_kb, the number should be equal to less than max_hw_sectors_kb, so your device may not allow setting it as 1024 this big.
echo 1024 > $Q/max_sectors_kb

echo 2 > $Q/rq_affinity
echo 2 > $Q/nomerges
echo 0 > $Q/rotational
echo 0 > $Q/add_random