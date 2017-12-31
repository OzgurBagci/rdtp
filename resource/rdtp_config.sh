#!/bin/sh

MY_HOSTNAME = $HOSTNAME | cut -d'.' -f1

if [MY_HOSTNAME == 's']; then
    route add d-link-2 gw r1-link-0
    route add d-link-3 gw r2-link-1
elif [MY_HOSTNAME == 'd']; then
    route add s-link-0 gw r1-link-2
    route add s-link-1 gw r2-link-3
fi