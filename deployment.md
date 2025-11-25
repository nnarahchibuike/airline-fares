# Deployment Guide

This guide explains how to deploy the Flight Scraper Telegram Bot to a VPS (Virtual Private Server) using Docker.

## Prerequisites

- A VPS with at least **1 vCPU** and **2GB RAM** (Recommended). 1GB RAM might work but could be unstable.
- Docker installed on the VPS.
- Your Telegram Bot Token.

## 1. Prepare the Server

SSH into your VPS and install Docker if you haven't already:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
```

## 2. Upload Code

You can upload your code using `scp` or `git`.

**Option A: Using Git (Recommended)**
1. Push your code to a private GitHub repo.
2. Clone it on the VPS:
   ```bash
   git clone https://github.com/yourusername/airline-scraper.git
   cd airline-scraper
   ```

**Option B: Using SCP (Copy from local)**
```bash
scp -r "Airline scraper" root@your_vps_ip:/root/airline-scraper
```

## 3. Configure Environment

Create the `.env` file on the server:

```bash
cd airline-scraper
nano .env
```

Paste your token:
```
TELEGRAM_BOT_TOKEN=your_actual_token_here
```
Save (Ctrl+O, Enter) and Exit (Ctrl+X).

## 4. Build and Run with Docker

Build the Docker image:
```bash
sudo docker build -t flight-bot .
```

Run the container in the background (detached mode):
```bash
sudo docker run -d --name flight-bot --env-file .env flight-bot
```

> **Note:** The Dockerfile now uses `start.sh` to configure the Timezone (default: Africa/Lagos) and Xvfb. This ensures correct currency detection (NGN) and browser stability.


## 5. Manage the Bot

**Check logs:**
```bash
sudo docker logs -f flight-bot
```

**Stop the bot:**
```bash
sudo docker stop flight-bot
```

**Restart the bot:**
```bash
sudo docker restart flight-bot
```

**Update the bot:**
1. Pull new code (`git pull`).
2. Rebuild image (`sudo docker build -t flight-bot .`).
3. Stop and remove old container (`sudo docker rm -f flight-bot`).
4. Run new container.

## Hardware Recommendations

- **CPU:** 1 vCPU is sufficient since scrapers run sequentially.
- **RAM:** **2GB is recommended**. Chrome is memory intensive.
  - If you only have 1GB RAM, you **must** enable a Swap file:
    ```bash
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    ```
