"""Test script for Emirates scraper only."""
from datetime import date
from core.models import FlightRequest
from core.orchestrator import FlightOrchestrator
from scrapers.emirates_scraper import EmiratesScraper


def main():
    """Test Emirates scraper."""
    # Create request
    request = FlightRequest(
        origin="LOS",
        destination="CAN",
        departure_date=date(2025, 12, 3),
        return_date=date(2025, 12, 23),
        adults=1
    )
    
    print("=" * 60)
    print("EMIRATES SCRAPER TEST")
    print("=" * 60)
    
    # Create orchestrator and register ONLY Emirates
    orchestrator = FlightOrchestrator()
    orchestrator.register_scraper(EmiratesScraper())
    
    # Run scraper
    print("Starting Emirates scrape...")
    results = orchestrator.scan_all(request)
    
    # Display results
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if not results:
        print("No flights found!")
    else:
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.airline}")
            print(f"   {result.departure_date} to {result.return_date}")
            print(f"   {result.price_display}")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
