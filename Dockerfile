FROM python:3.13-slim

LABEL MAINTAINER "mark.hsieh <qqzcmark@gmail.com>"

USER root

## install package
RUN apt-get update && apt-get install -y \
    procps \
    net-tools \
    bash \
    tzdata \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/local/app
WORKDIR /usr/local

## setting network
COPY utility_loopback.sh .
RUN chmod +x ./utility_loopback.sh
RUN ./utility_loopback.sh

COPY utility_namespace_dns.sh .
RUN chmod +x ./utility_namespace_dns.sh
RUN ./utility_namespace_dns.sh

## install python package
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
