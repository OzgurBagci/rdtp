#!/bin/sh

apt-get install software-properties-common
add-apt-repository ppa:jonathonf/python-3.6
apt-get update
apt-get install python3.6
./rdtp_config
gcc ../source/sctp/sctp/client.c -lsctp -o client.o
gcc ../source/sctp/sctp/server.c -lsctp -o server.o
python3.6 ../setup.py install
