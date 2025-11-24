"""Entry point for the flight scraper bot."""
import os
import sys
from dotenv import load_dotenv

# Add current directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.telegram_bot import main

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run bot
    main()
