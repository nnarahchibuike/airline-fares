"""Emirates airline scraper."""
from typing import List
from datetime import date
import logging
import os
from seleniumbase import SB
from bs4 import BeautifulSoup

from scrapers.base_scraper import AirlineScraper
from core.models import FlightRequest, FlightResult

# Set up logger
logger = logging.getLogger(__name__)


class EmiratesScraper(AirlineScraper):
    """Scraper for Emirates airline."""
    
    def __init__(self):
        """Initialize Emirates scraper."""
        super().__init__("Emirates")
    
    def scrape(self, request: FlightRequest) -> List[FlightResult]:
        """
        Scrape Emirates flights.
        
        Args:
            request: FlightRequest with search parameters
            
        Returns:
            List of FlightResult objects
        """
        results = []
        
        with SB(uc=True, test=False, locale="en", ad_block=True, xvfb=True, chromium_arg="--disable-dev-shm-usage") as sb:
            # Force desktop layout to prevent mobile view issues
            sb.set_window_size(1920, 1080)
            # Navigate and fill form
            url = "https://www.emirates.com/ng/english/book/"
            logger.info(f"Opening Emirates booking page: {url}")
            sb.open(url)
            sb.sleep(10)  # Increased from 6s
            
            # Handle cookies
            sb.click_if_visible("button#onetrust-accept-btn-handler")
            sb.click_if_visible('button:contains("Accept")')
            sb.click_if_visible('button[aria-label*="Accept"]')
            sb.sleep(3)
            
            # Set origin
            sb.click('input[id^="auto-suggest_"]:first-of-type')
            sb.sleep(2)
            sb.type('input[id^="auto-suggest_"]:first-of-type', request.origin)
            sb.sleep(3)
            sb.click('li[role="option"]:first-child')
            sb.sleep(2)
            
            # Set destination
            arrival_id = sb.execute_script(
                "return document.querySelectorAll(\"input[id^='auto-suggest_']\")[1].id"
            )
            sb.sleep(2)
            sb.click(f"#{arrival_id}")
            sb.sleep(2)
            sb.type(f"#{arrival_id}", request.destination + "\n")
            sb.sleep(3)
            
            # Enable flexible dates
            sb.click('button.custom-switch__toggle')
            sb.sleep(2)
            
            # Set dates (using React value setter hack)
            dep_date_str = request.departure_date.strftime("%d %b %y")
            ret_date_str = request.return_date.strftime("%d %b %y")
            
            # Set departure date
            sb.click('#startDate')
            sb.sleep(3)
            sb.execute_script(f"""
                var input = document.querySelector('#startDate');
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                nativeInputValueSetter.call(input, '{dep_date_str}');
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                input.dispatchEvent(new Event('blur', {{ bubbles: true }}));
            """)
            sb.sleep(2)
            
            # Set return date
            sb.click('#endDate')
            sb.sleep(3)
            sb.execute_script(f"""
                var input = document.querySelector('#endDate');
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                nativeInputValueSetter.call(input, '{ret_date_str}');
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                input.dispatchEvent(new Event('blur', {{ bubbles: true }}));
            """)
            sb.sleep(3)
            
            # Search
            try:
                # Try multiple selectors for the search button
                if sb.is_element_visible('button.rsw-submit-button'):
                    sb.click('button.rsw-submit-button')
                elif sb.is_element_visible('button[type="submit"]'):
                    sb.click('button[type="submit"]')
                elif sb.is_element_visible('button:contains("Search flights")'):
                    sb.click('button:contains("Search flights")')
                else:
                    raise Exception("Search button not found")
                    
                sb.sleep(20)  # Increased from 10s
            except Exception as e:
                logger.error(f"Failed to click search button: {e}")
                # Debug: Save screenshot and HTML on failure
                try:
                    screenshot_dir = "/app/downloaded_files"
                    os.makedirs(screenshot_dir, exist_ok=True)
                    screenshot_path = f"{screenshot_dir}/emirates_search_btn_fail_{request.origin}_{request.destination}.png"
                    html_path = f"{screenshot_dir}/emirates_search_btn_fail_{request.origin}_{request.destination}.html"
                    
                    sb.save_screenshot(screenshot_path)
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(sb.get_page_source())
                    logger.info(f"Debug files saved: {screenshot_path}, {html_path}")
                    
                    # Raise ScraperError with artifacts
                    from core.exceptions import ScraperError
                    raise ScraperError(f"Search button not found: {e}", screenshot_path, html_path)
                    
                except Exception as debug_error:
                    logger.error(f"Failed to save debug files: {debug_error}")
                    # If we can't save debug files, just re-raise the original error or a generic one
                    raise e
                return results
            
            # Extract results
            try:
                logger.info("Waiting for calendar grid element...")
                sb.wait_for_element('.calendar-grid', timeout=60)  # Increased timeout for Docker
                logger.info("Calendar grid found successfully")
            except Exception as e:
                logger.error(f"Failed to find calendar grid: {e}")
                # Debug: Save screenshot and HTML on failure
                try:
                    screenshot_dir = "/app/downloaded_files"
                    os.makedirs(screenshot_dir, exist_ok=True)
                    screenshot_path = f"{screenshot_dir}/emirates_calendar_debug_{request.origin}_{request.destination}.png"
                    html_path = f"{screenshot_dir}/emirates_calendar_debug_{request.origin}_{request.destination}.html"
                    
                    sb.save_screenshot(screenshot_path)
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(sb.get_page_source())
                    logger.info(f"Debug files saved: {screenshot_path}, {html_path}")
                except Exception as debug_error:
                    logger.error(f"Failed to save debug files: {debug_error}")
                return results
            
            soup = BeautifulSoup(sb.get_page_source(), 'html.parser')
            
            # Extract origin and destination
            ond_elements = soup.select('.search-details__ond span[aria-hidden="true"]')
            origin_name = ond_elements[0].text.strip() if ond_elements else request.origin
            dest_name = ond_elements[-1].text.strip() if ond_elements else request.destination
            
            # Parse dates
            def parse_date(text, prefix):
                clean_text = text.replace(prefix, "").strip()
                parts = clean_text.split()
                if len(parts) >= 3:
                    return f"{parts[2]} {parts[1]}"
                return clean_text
            
            # Extract outbound dates (columns)
            outbound_dates = []
            headers = soup.select('thead th .aa-hidden')
            for header in headers:
                text = header.text.strip()
                if "Outbound" in text:
                    outbound_dates.append(parse_date(text, "Outbound"))
            
            # Extract prices from grid
            rows = soup.select('tbody tr')
            for row_idx, row in enumerate(rows):
                row_header = row.select_one('th[scope="row"] .aa-hidden')
                if not row_header:
                    continue
                inbound_date = parse_date(row_header.text.strip(), "Inbound")
                
                cells = row.select('td')
                for col_idx, cell in enumerate(cells):
                    if col_idx >= len(outbound_dates):
                        break
                    
                    outbound_date = outbound_dates[col_idx]
                    
                    # Skip unavailable
                    if 'calendar-cell--no-available' in cell.get('class', []):
                        continue
                    
                    # Extract price
                    amount_el = cell.select_one('.line-cash--amount')
                    currency_el = cell.select_one('.line-cash--currency')
                    
                    if amount_el and currency_el:
                        currency = currency_el.text.strip()
                        amount_text = amount_el.text.strip()
                        price_numeric = float(amount_text.replace(',', ''))
                        
                        # Check if lowest
                        lowest_div = cell.select_one('.lowest-price')
                        is_lowest = lowest_div and "Lowest price" in lowest_div.text
                        
                        result = FlightResult(
                            airline=self.name,
                            origin=origin_name,
                            destination=dest_name,
                            departure_date=outbound_date,
                            return_date=inbound_date,
                            price=price_numeric,
                            currency=currency,
                            price_display=f"{currency} {amount_text}",
                            is_lowest=is_lowest
                        )
                        results.append(result)
        
        return results
