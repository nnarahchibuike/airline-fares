"""Test script for unified flight scanner."""
from datetime import date
from core.models import FlightRequest
from core.orchestrator import FlightOrchestrator
from scrapers.emirates_scraper import EmiratesScraper
from scrapers.ethiopian_scraper import EthiopianScraper
from scrapers.qatar_scraper import QatarScraper


def main():
    """Test concurrent scraping of all airlines."""
    # Create request
    request = FlightRequest(
        origin="LOS",
        destination="CAN",
        departure_date=date(2025, 12, 3),
        return_date=date(2025, 12, 23),
        adults=1
    )
    
    print("=" * 60)
    print("FLIGHT SCANNER TEST")
    print("=" * 60)
    print(f"Route: {request.origin} → {request.destination}")
    print(f"Depart: {request.departure_date}")
    print(f"Return: {request.return_date}")
    print("=" * 60)
    print()
    
    # Create orchestrator and register scrapers
    orchestrator = FlightOrchestrator()
    orchestrator.register_scraper(EmiratesScraper())
    orchestrator.register_scraper(EthiopianScraper())
    orchestrator.register_scraper(QatarScraper())
    
    # Run all scrapers concurrently
    print("Starting concurrent scraping...")
    print()
    results = orchestrator.scan_all(request)
    
    # Display results
    print()
    print("=" * 60)
    print("RESULTS (sorted by price)")
    print("=" * 60)
    
    if not results:
        print("No flights found!")
    else:
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.airline}")
            print(f"   {result.departure_date} to {result.return_date}")
            print(f"   {result.price_display}{'  ⭐ BEST PRICE' if i == 1 else ''}")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
