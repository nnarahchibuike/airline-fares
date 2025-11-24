"""Base scraper abstract class."""
from abc import ABC, abstractmethod
from typing import List, Optional
import logging
from core.models import FlightRequest, FlightResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AirlineScraper(ABC):
    """Abstract base class for airline scrapers."""
    
    def __init__(self, name: str):
        """Initialize scraper with airline name."""
        self.name = name
    
    @abstractmethod
    def scrape(self, request: FlightRequest) -> List[FlightResult]:
        """
        Scrape flights for the given request.
        
        Args:
            request: FlightRequest with search parameters
            
        Returns:
            List of FlightResult objects
            
        Raises:
            Exception: If scraping fails
        """
        pass
    
    def get_best_price(self, request: FlightRequest) -> Optional[FlightResult]:
        """
        Get the cheapest flight for the given request.
        
        Args:
            request: FlightRequest with search parameters
            
        Returns:
            FlightResult with lowest price, or None if no flights found
        """
        logger = logging.getLogger(f"{__name__}.{self.name}")
        try:
            logger.info(f"Scraping {self.name}...")
            results = self.scrape(request)
            
            if not results:
                logger.warning(f"No flights found on {self.name}")
                return None
            
            best = min(results, key=lambda x: x.price)
            logger.info(f"{self.name} best price: {best.price_display}")
            return best
            
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {e}")
            return None
