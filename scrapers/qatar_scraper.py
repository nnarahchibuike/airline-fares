"""Qatar Airways scraper."""
from typing import List
from seleniumbase import SB
from bs4 import BeautifulSoup

from scrapers.base_scraper import AirlineScraper
from core.models import FlightRequest, FlightResult


class QatarScraper(AirlineScraper):
    """Scraper for Qatar Airways."""
    
    def __init__(self):
        """Initialize Qatar scraper."""
        super().__init__("Qatar")
    
    def scrape(self, request: FlightRequest) -> List[FlightResult]:
        """
        Scrape Qatar Airways flights.
        
        Args:
            request: FlightRequest with search parameters
            
        Returns:
            List of FlightResult objects
        """
        results = []
        
        with SB(uc=True, test=False, locale="en", ad_block=True, args=["--disable-dev-shm-usage"]) as sb:
            # Build deep link URL
            url = (
                f"https://www.qatarairways.com/app/booking/flight-selection"
                f"?widget=QR"
                f"&searchType=F"
                f"&addTaxToFare=Y"
                f"&minPurTime=0"
                f"&selLang=en"
                f"&tripType=R"
                f"&fromStation={request.origin}"
                f"&toStation={request.destination}"
                f"&departing={request.departure_date.strftime('%Y-%m-%d')}"
                f"&returning={request.return_date.strftime('%Y-%m-%d')}"
                f"&bookingClass=E"
                f"&adults={request.adults}"
                f"&children=0"
                f"&infants=0"
                f"&ofw=0"
                f"&teenager=0"
                f"&flexibleDate=true"
                f"&allowRedemption=N"
            )
            
            sb.open(url)
            sb.sleep(10)
            
            # Handle cookies
            sb.click_if_visible("button#onetrust-accept-btn-handler")
            sb.sleep(3)
            sb.click_if_visible('button:contains("Accept")')
            sb.click_if_visible('button[aria-label*="Accept"]')
            sb.click_if_visible('button:contains("Accept all cookies")')
            sb.sleep(3)
            
            # Wait for calendar
            sb.wait_for_element('flexible-calendar', timeout=20)
            sb.sleep(5)
            
            # Parse results
            soup = BeautifulSoup(sb.get_page_source(), 'html.parser')
            
            # Extract departure dates (column headers)
            departure_dates = []
            dep_headers = soup.select('.calendar-head-hor .ch span')
            for header in dep_headers:
                date_text = header.text.strip()
                if date_text and ',' in date_text:
                    parts = date_text.split(',')
                    if len(parts) > 1:
                        departure_dates.append(parts[1].strip())
            
            # Extract return dates (row headers)
            return_dates = []
            ret_headers = soup.select('.calendar-head-ver .ch span')
            for header in ret_headers:
                date_text = header.text.strip()
                if date_text and ',' in date_text:
                    parts = date_text.split(',')
                    if len(parts) > 1:
                        return_dates.append(parts[1].strip())
            
            # Process each row
            rows = soup.select('.cr')
            for row_idx, row in enumerate(rows):
                if row_idx >= len(return_dates):
                    break
                
                ret_date = return_dates[row_idx]
                
                # Get all price cells in this row
                cells = row.select('.cd.has-price')
                for col_idx, cell in enumerate(cells):
                    if col_idx >= len(departure_dates):
                        break
                    
                    dep_date = departure_dates[col_idx]
                    
                    # Extract price
                    currency_el = cell.select_one('.long-currency-symbol')
                    amount_el = cell.select_one('span[dir="ltr"]')
                    
                    if currency_el and amount_el:
                        currency = currency_el.text.strip()
                        amount_text = amount_el.text.strip()
                        
                        # Parse numeric price (handle M/K suffixes)
                        try:
                            if 'M' in amount_text:
                                price_numeric = float(amount_text.replace('M', '').replace(',', '')) * 1000000
                            elif 'K' in amount_text:
                                price_numeric = float(amount_text.replace('K', '').replace(',', '')) * 1000
                            else:
                                price_numeric = float(amount_text.replace(',', ''))
                        except:
                            continue
                        
                        # Check if lowest
                        is_lowest = cell.select_one('.lowest') is not None
                        
                        result = FlightResult(
                            airline=self.name,
                            origin=request.origin,
                            destination=request.destination,
                            departure_date=dep_date,
                            return_date=ret_date,
                            price=price_numeric,
                            currency=currency,
                            price_display=f"{currency} {amount_text}",
                            is_lowest=is_lowest
                        )
                        results.append(result)
        
        return results
