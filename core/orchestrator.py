"""Orchestrator for running multiple scrapers concurrently."""
import asyncio
import concurrent.futures
from typing import List, Dict
import logging
from scrapers.base_scraper import AirlineScraper
from core.models import FlightRequest, FlightResult

logger = logging.getLogger(__name__)


from core.exceptions import ScraperError

class FlightOrchestrator:
    """Manages concurrent execution of multiple airline scrapers."""
    
    def __init__(self):
        """Initialize orchestrator with empty scraper list."""
        self.scrapers: List[AirlineScraper] = []
    
    def register_scraper(self, scraper: AirlineScraper):
        """
        Register a new airline scraper.
        
        Args:
            scraper: AirlineScraper instance to register
        """
        self.scrapers.append(scraper)
        logger.info(f"Registered scraper: {scraper.name}")
    
    def scan_all(self, request: FlightRequest) -> tuple[Dict[str, List[FlightResult]], List[Dict]]:
        """
        Run all registered scrapers concurrently using multiprocessing.
        
        Args:
            request: FlightRequest with search parameters
            
        Returns:
            Tuple containing:
            - Dictionary mapping airline name to list of FlightResult objects.
            - List of error dictionaries with keys: airline, message, screenshot_path
        """
        logger.info(f"Scanning {len(self.scrapers)} airlines in parallel...")
        
        results_by_airline = {}
        errors = []
        
        # Run scrapers in separate processes
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # Submit tasks - call scrape() instead of get_best_price()
            future_to_scraper = {
                executor.submit(scraper.scrape, request): scraper 
                for scraper in self.scrapers
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_scraper):
                scraper = future_to_scraper[future]
                try:
                    airline_results = future.result()
                    if not airline_results:
                        continue
                        
                    # Sort by price
                    airline_results.sort(key=lambda x: x.price)
                    
                    # Find exact date match
                    exact_match = None
                    
                    # Generate possible date strings for matching
                    # e.g. "Dec 3", "Dec 03", "December 3", "December 03"
                    dep_formats = [
                        request.departure_date.strftime("%b %-d"),
                        request.departure_date.strftime("%b %d"),
                        request.departure_date.strftime("%B %-d"),
                        request.departure_date.strftime("%B %d")
                    ]
                    ret_formats = [
                        request.return_date.strftime("%b %-d"),
                        request.return_date.strftime("%b %d"),
                        request.return_date.strftime("%B %-d"),
                        request.return_date.strftime("%B %d")
                    ]
                    
                    # Helper to check if date string matches any format
                    def is_match(date_str, formats):
                        return any(fmt in date_str for fmt in formats)
                    
                    # Search for exact match
                    for r in airline_results:
                        if is_match(r.departure_date, dep_formats) and is_match(r.return_date, ret_formats):
                            exact_match = r
                            break
                    
                    final_list = []
                    
                    # Add exact match first if found
                    if exact_match:
                        final_list.append(exact_match)
                        # Remove exact match from pool to avoid duplicate in top 9
                        airline_results.remove(exact_match)
                    
                    # Add top 9 cheapest
                    final_list.extend(airline_results[:9])
                    
                    results_by_airline[scraper.name] = final_list
                    
                except ScraperError as se:
                    logger.error(f"Scraper {scraper.name} failed with artifacts: {se}")
                    errors.append({
                        "airline": scraper.name,
                        "message": str(se),
                        "screenshot_path": se.screenshot_path
                    })
                except Exception as e:
                    logger.error(f"Scraper {scraper.name} failed: {e}")
                    errors.append({
                        "airline": scraper.name,
                        "message": str(e),
                        "screenshot_path": None
                    })
        
        return results_by_airline, errors
