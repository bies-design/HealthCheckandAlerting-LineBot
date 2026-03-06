#!/bin/bash

# catch global variables from .env file
PORT=`grep -r "SERVER_PORT" app/.env | sed  's|.*=||g'`

# start the server
gunicorn -w 1 -b 0.0.0.0:${PORT} app.__main__:app