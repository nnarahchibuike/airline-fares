#!/bin/bash

# Setup Script for Airline Scraper on Ubuntu VPS
# Run this as root or with sudo

set -e  # Exit on error

echo "Starting setup..."

# 1. System Update & Dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y \
    wget \
    gnupg \
    unzip \
    xvfb \
    dbus \
    libxi6 \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    default-jdk \
    python3-tk \
    python3-dev \
    python3-venv \
    python3-pip \
    locales \
    tzdata \
    git \
    tmux

# 2. Configure Timezone & Locale
echo "Configuring Timezone and Locale..."
timedatectl set-timezone Africa/Lagos
locale-gen en_US.UTF-8
update-locale LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# 3. Install Google Chrome
echo "Installing Google Chrome..."
if ! command -v google-chrome &> /dev/null; then
    install -m 0755 -d /etc/apt/keyrings
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
    apt-get update
    apt-get install -y google-chrome-stable
else
    echo "Google Chrome is already installed."
fi

# 4. Python Environment Setup
echo "Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate venv and install dependencies
source venv/bin/activate

echo "Installing Python packages..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found!"
fi
pip install seleniumbase

# Install chromedriver
echo "Installing Chromedriver..."
seleniumbase install chromedriver

echo "Setup complete!"
echo "To run the bot:"
echo "1. Create your .env file"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python main.py"
