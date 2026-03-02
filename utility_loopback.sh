#!/bin/bash

if [ ! -e "/etc/network/interfaces" ]; then
    touch /etc/network/interfaces
fi

if [ -e "/etc/network/interfaces" ]; then
    echo "auto lo" | tee -a /etc/network/interfaces >/dev/null
    echo "iface lo inet loopback" | tee -a /etc/network/interfaces >/dev/null
fi