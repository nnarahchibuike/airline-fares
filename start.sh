#!/bin/bash

# Generate machine-id to prevent Chrome/DBus errors
dbus-uuidgen > /etc/machine-id

# Set timezone to Lagos for correct currency/locale detection
export TZ=Africa/Lagos

# Start Xvfb
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
export DISPLAY=:99

# Wait for Xvfb to start
sleep 2

# Run the bot
python main.py
