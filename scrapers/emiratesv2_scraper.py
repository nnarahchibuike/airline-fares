"""Emirates V2 scraper using deep link approach."""
from typing import List
from seleniumbase import SB
from bs4 import BeautifulSoup

from scrapers.base_scraper import AirlineScraper
from core.models import FlightRequest, FlightResult


class EmiratesV2Scraper(AirlineScraper):
    """Simple Emirates scraper using deep link with minimal resource usage."""
    
    def __init__(self):
        """Initialize EmiratesV2 scraper."""
        super().__init__("EmiratesV2")
    
    def scrape(self, request: FlightRequest) -> List[FlightResult]:
        """
        Scrape Emirates flights using deep link.
        
        Note: This scraper only checks the specific return date provided,
        not a flexible calendar like some other scrapers.
        
        Args:
            request: FlightRequest with search parameters
            
        Returns:
            List of FlightResult objects (typically just one result)
        """
        results = []
        
        # Using regular mode (not uc=True) for much faster startup
        # Headless mode also speeds things up
        # xvfb=True handles virtual display in Docker
        with SB(test=False, headless=True, ad_block=True, xvfb=True) as sb:
            # Force desktop layout to prevent mobile view issues
            sb.set_window_size(1920, 1080)
            # Build deep link URL
            # Format dates as DD-Mon-YY (e.g., 21-Dec-25)
            dep_date = request.departure_date.strftime("%d-%b-%y")
            ret_date = request.return_date.strftime("%d-%b-%y")
            
            url = (
                f"https://www.emirates.com/booking/search-results/"
                f"?seladults={request.adults}"
                f"&seldcity1={request.origin}"
                f"&selchildren=0"
                f"&flyOption=0"
                f"&TID=SB"
                f"&selddate1={dep_date}"
                f"&Tab=2"
                f"&seladate1={ret_date}"
                f"&selcabinclass=0"
                f"&selinfants=0"
                f"&publisher=1101ldFz"
                f"&pub=%2Fng%2Fenglish"
                f"&selacity1={request.destination}"
            )
            
            sb.open(url)
            sb.sleep(2)  # Minimal wait
            
            # Handle cookie consent if present
            try:
                sb.click_if_visible('button[id*="accept"]', timeout=2)
                sb.click_if_visible('button:contains("Accept")', timeout=1)
            except:
                pass
            
            # Wait for price element to load
            try:
                sb.wait_for_element('span.currency-cash__amount', timeout=8)
            except:
                # If element doesn't appear in time, return empty results
                return results
            
            # Parse the page
            soup = BeautifulSoup(sb.get_page_source(), 'html.parser')
            
            # Extract price from the currency-cash__amount span
            price_element = soup.select_one('span.currency-cash__amount')
            
            if price_element:
                price_text = price_element.text.strip()
                
                # Parse numeric price (remove commas)
                try:
                    price_numeric = float(price_text.replace(',', ''))
                except ValueError:
                    # If parsing fails, skip this result
                    return results
                
                # Try to find currency symbol
                # Look for currency symbol in parent or nearby elements
                currency = "NGN"  # Default to NGN based on the URL pub parameter
                currency_element = soup.select_one('span.currency-cash__currency')
                if currency_element:
                    currency = currency_element.text.strip()
                
                # Format dates for display
                dep_display = request.departure_date.strftime("%d %b %Y")
                ret_display = request.return_date.strftime("%d %b %Y")
                
                result = FlightResult(
                    airline=self.name,
                    origin=request.origin,
                    destination=request.destination,
                    departure_date=dep_display,
                    return_date=ret_display,
                    price=price_numeric,
                    currency=currency,
                    price_display=f"{currency} {price_text}",
                    is_lowest=False  # Single result, so not comparing
                )
                results.append(result)
        
        return results

