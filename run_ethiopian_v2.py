import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.ethiopianv2_scraper_prototype import EthiopianV2ScraperPrototype
from core.models import FlightRequest
from datetime import date

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("Starting Ethiopian V2 Prototype Test...")
    scraper = EthiopianV2ScraperPrototype()
    
    # Request params are mostly ignored due to hardcoding in prototype
    request = FlightRequest(
        origin="LOS",
        destination="CAN",
        departure_date=date(2026, 1, 4),
        return_date=date(2026, 1, 21),
        adults=1
    )
    
    try:
        results = scraper.scrape(request)
        print(f"Scrape completed. Found {len(results)} results.")
    except Exception as e:
        print(f"Scrape failed: {e}")

if __name__ == "__main__":
    main()
