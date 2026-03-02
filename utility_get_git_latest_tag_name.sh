#!/bin/bash

_TAG=`git describe --tags --abbrev=0 2>/dev/null`
if [ ! -z "${_TAG}" ]; then
    #echo "the latest tag name is: ${_TAG}"
    echo "${_TAG}"
else
    #echo "no tag name exist. we use the default tag name: dev"
    echo "dev"
fi