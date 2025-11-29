"""Ethiopian Airlines scraper."""
from typing import List
from seleniumbase import SB
from bs4 import BeautifulSoup

import os
import logging
from scrapers.base_scraper import AirlineScraper
from core.models import FlightRequest, FlightResult
from core.exceptions import ScraperError

logger = logging.getLogger(__name__)

class EthiopianScraper(AirlineScraper):
    """Scraper for Ethiopian Airlines."""
    
    def __init__(self):
        """Initialize Ethiopian scraper."""
        super().__init__("Ethiopian")
    
    def scrape(self, request: FlightRequest) -> List[FlightResult]:
        """
        Scrape Ethiopian Airlines flights.
        
        Args:
            request: FlightRequest with search parameters
            
        Returns:
            List of FlightResult objects
        """
        results = []
        
        with SB(uc=True, test=False, locale="en", ad_block=False, chromium_arg="--disable-dev-shm-usage") as sb:
            # Track screenshots for debugging
            progress_screenshots = []
            
            def take_screenshot(step_name):
                try:
                    screenshot_dir = "/app/downloaded_files"
                    os.makedirs(screenshot_dir, exist_ok=True)
                    # Use a counter to ensure order
                    count = len(progress_screenshots) + 1
                    screenshot_path = f"{screenshot_dir}/ethiopian_step_{count}_{step_name}_{request.origin}_{request.destination}.png"
                    sb.save_screenshot(screenshot_path)
                    progress_screenshots.append(screenshot_path)
                    logger.info(f"Saved debug screenshot: {screenshot_path}")
                except Exception as e:
                    logger.error(f"Failed to take screenshot for {step_name}: {e}")

            try:
                take_screenshot("0_start")
                # Build deep link URL
                url = (
                    f"https://dxbooking.ethiopianairlines.com/dx/ETDX/#/matrix"
                    f"?journeyType=round-trip"
                    f"&activeMonth={request.departure_date.strftime('%m-%d-%Y')}"
                    f"&awardBooking=false"
                    f"&searchType=BRANDED"
                    f"&class=Economy"
                    f"&ADT={request.adults}"
                    f"&C13=0"
                    f"&CHD=0"
                    f"&INF=0"
                    f"&origin={request.origin}"
                    f"&destination={request.destination}"
                    f"&date={request.departure_date.strftime('%m-%d-%Y')}"
                    f"&origin1={request.destination}"
                    f"&destination1={request.origin}"
                    f"&date1={request.return_date.strftime('%m-%d-%Y')}"
                    f"&direction=0"
                )
                
                logger.info(f"Opening URL: {url}")
                sb.open(url)
                sb.sleep(10)
                take_screenshot("1_loaded_page")
                
                # Handle cookies
                sb.click_if_visible("button#onetrust-accept-btn-handler")
                sb.click_if_visible('button:contains("Accept")')
                sb.click_if_visible('button[aria-label*="Accept"]')
                sb.sleep(3)
                take_screenshot("2_cookies_handled")
                
                # Wait for results
                # Wait for results
                logger.info("Waiting for matrix grid...")
                try:
                    sb.wait_for_element('.dxp-matrix-grid-layout', timeout=60)
                    sb.sleep(30)  # Wait for full page load
                    take_screenshot("3_matrix_loaded")
                except Exception as e:
                    logger.error(f"Timeout waiting for matrix: {e}")
                    
                    # Debug artifacts
                    screenshot_dir = "/app/downloaded_files"
                    os.makedirs(screenshot_dir, exist_ok=True)
                    screenshot_path = f"{screenshot_dir}/ethiopian_timeout_{request.origin}_{request.destination}.png"
                    html_path = f"{screenshot_dir}/ethiopian_timeout_{request.origin}_{request.destination}.html"
                    
                    sb.save_screenshot(screenshot_path)
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(sb.get_page_source())
                        
                    raise ScraperError(f"Timeout waiting for matrix: {e}", screenshot_path, html_path, progress_screenshots)
                
                # Parse results
                soup = BeautifulSoup(sb.get_page_source(), 'html.parser')
                
                # Extract outbound dates (column headers)
                outbound_dates = []
                headers = soup.select('thead th.date-header .date .number')
                for header in headers:
                    date_text = header.text.strip()
                    if date_text and "Invalid" not in date_text:
                        outbound_dates.append(date_text)
                    else:
                        outbound_dates.append(None)
                
                # Extract rows
                rows = soup.select('tbody tr')
                for row_idx, row in enumerate(rows):
                    row_header = row.select_one('th .date .number')
                    if not row_header:
                        continue
                    return_date = row_header.text.strip()
                    
                    if "Invalid" in return_date:
                        continue
                    
                    cells = row.select('td')
                    for col_idx, cell in enumerate(cells):
                        if col_idx >= len(outbound_dates):
                            break
                        
                        depart_date = outbound_dates[col_idx]
                        if not depart_date:  # Skip invalid columns
                            continue
                        
                        # Check if sold out
                        button = cell.select_one('button')
                        if button and 'no-flights' in button.get('class', []):
                            continue
                        
                        # Extract price
                        amount_el = cell.select_one('.amount .number')
                        currency_el = cell.select_one('.currency.symbol')
                        
                        if amount_el and currency_el:
                            currency = currency_el.text.strip()
                            amount_text = amount_el.text.strip()
                            price_numeric = float(amount_text.replace(',', ''))
                            
                            # Check for lowest fare
                            is_lowest = button and 'lowest-fare' in button.get('class', [])
                            
                            result = FlightResult(
                                airline=self.name,
                                origin=f"{request.origin}",
                                destination=f"{request.destination}",
                                departure_date=depart_date,
                                return_date=return_date,
                                price=price_numeric,
                                currency=currency,
                                price_display=f"{currency} {amount_text}",
                                is_lowest=is_lowest,
                                screenshot_paths=progress_screenshots
                            )
                            results.append(result)
            
            except ScraperError:
                raise
            except Exception as e:
                logger.error(f"Error during Ethiopian scrape: {e}")
                
                # Debug artifacts
                screenshot_dir = "/app/downloaded_files"
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_path = f"{screenshot_dir}/ethiopian_error_{request.origin}_{request.destination}.png"
                html_path = f"{screenshot_dir}/ethiopian_error_{request.origin}_{request.destination}.html"
                
                try:
                    sb.save_screenshot(screenshot_path)
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(sb.get_page_source())
                except:
                    pass
                    
                raise ScraperError(f"Ethiopian scrape failed: {e}", screenshot_path, html_path, progress_screenshots)
            
            if not results:
                logger.warning("No results found. Saving screenshot.")
                take_screenshot("4_no_results")
        
        return results
