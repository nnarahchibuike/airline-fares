# Deployment Guide for Airline Scraper (Non-Docker)

This guide details how to deploy your airline scraper directly onto a VPS (Virtual Private Server) running Ubuntu (22.04 or 24.04 recommended). This method allows you to run the scraper natively, which can be easier to debug and manage than Docker for some users.

## Prerequisites

- A VPS running **Ubuntu 20.04 LTS**, **22.04 LTS**, or **24.04 LTS**.
- Root access or a user with `sudo` privileges.

## Step 1: System Update & Dependencies

The provided `setup_vps.sh` script handles all of this for you.

If you prefer to run commands manually, install system libraries:

```bash
sudo apt-get update
sudo apt-get install -y \
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
```

## Step 2: Configure Timezone & Locale

Set the timezone to Lagos (as per your Dockerfile) and ensure the locale is correct.

```bash
# Set Timezone
sudo timedatectl set-timezone Africa/Lagos

# Generate Locale
sudo locale-gen en_US.UTF-8
sudo update-locale LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

## Step 3: Install Google Chrome

SeleniumBase needs Google Chrome to run.

```bash
# Download Google's signing key
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg

# Add the repository
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# Install Chrome
sudo apt-get update
sudo apt-get install -y google-chrome-stable
```

## Step 4: Project Setup

1.  **Copy your files** to the VPS. You can use `git clone` if your repo is on GitHub, or `scp` to copy files from your local machine.

    ```bash
    # Example using git (replace with your actual repo URL)
    git clone https://github.com/yourusername/airline-scraper.git
    cd airline-scraper
    ```

    *Or if copying manually, create a directory and upload files there.*

2.  **Create a Virtual Environment**:
    It's best practice to use a virtual environment to avoid conflicting with system Python packages.

    ```bash
    python3.12 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python Dependencies**:

    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install seleniumbase
    ```

4.  **Install Chromedriver**:
    SeleniumBase can automatically manage this, but running this command ensures it's set up.

    ```bash
    seleniumbase install chromedriver
    ```

## Step 5: Configuration

Create your `.env` file with the necessary secrets.

```bash
nano .env
```

Paste your environment variables (e.g., `TELEGRAM_BOT_TOKEN`, `PROXY_URL`, etc.) into this file and save it (`Ctrl+X`, `Y`, `Enter`).

## Step 6: Running the Scraper

You can now run the scraper.

```bash
python main.py
```

### "Allowing Chrome Tabs to Open Comfortably"

Your code currently has `headless=True` and `xvfb=True` in `scrapers/emiratesv2_scraper.py`.

*   **If you want to run it purely headless (background):** Keep the settings as they are. The `xvfb` support in SeleniumBase will handle the virtual display.
*   **If you want to SEE the browser (GUI):**
    1.  You need to connect to your VPS with **X11 Forwarding** enabled.
        *   **Mac/Linux**: `ssh -X user@your-vps-ip`
        *   **Windows**: Use PuTTY with X11 forwarding enabled and run Xming or VcXsrv on your PC.
    2.  Edit `scrapers/emiratesv2_scraper.py`:
        *   Set `headless=False`
        *   Set `xvfb=False` (since you are forwarding the display)
    3.  Run `python main.py`. The Chrome window should appear on your local computer.

## Step 7: Keeping it Running (Production)

To keep the bot running after you disconnect from SSH, use `tmux`.

1.  Start a new session:
    ```bash
    tmux new -s scraper
    ```
2.  Activate venv and run the bot:
    ```bash
    source venv/bin/activate
    python main.py
    ```
3.  **Detach** from the session by pressing `Ctrl+B`, then `D`. The bot will keep running in the background.
4.  To **reattach** later to check logs or status:
    ```bash
    tmux attach -t scraper
    ```
