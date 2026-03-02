#!/bin/bash 

if [ ! -e "/etc/resolv.conf" ]; then
  touch /etc/resolv.conf
  chmod +rw /etc/resolv.conf
  echo "nameserver 8.8.8.8 " | tee -a /etc/resolv.conf >/dev/null
  echo "nameserver 168.95.1.1 " | tee -a /etc/resolv.conf >/dev/null
  echo "nameserver 61.31.1.1 " | tee -a /etc/resolv.conf >/dev/null
  echo "nameserver 208.67.222.222 " | tee -a /etc/resolv.conf >/dev/null
else
  cat /etc/resolv.conf
fi