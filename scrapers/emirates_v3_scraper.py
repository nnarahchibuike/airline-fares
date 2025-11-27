"""Emirates V3 scraper for homepage widget."""
from typing import List
import logging
import os
from seleniumbase import SB
from bs4 import BeautifulSoup

from scrapers.base_scraper import AirlineScraper
from core.models import FlightRequest, FlightResult
from core.exceptions import ScraperError

# Set up logger
logger = logging.getLogger(__name__)


class EmiratesV3Scraper(AirlineScraper):
    """Scraper for Emirates homepage widget (V3)."""
    
    def __init__(self):
        """Initialize Emirates V3 scraper."""
        super().__init__("EmiratesV3")
    
    def scrape(self, request: FlightRequest) -> List[FlightResult]:
        """
        Scrape Emirates flights starting from homepage.
        
        Args:
            request: FlightRequest with search parameters
            
        Returns:
            List of FlightResult objects
        """
        results = []
        
        # Proxy configuration
        proxy_auth = os.getenv("PROXY_URL")
        
        sb_args = {
            "uc": True,
            "test": False,
            "locale": "en",
            "ad_block": True,
            "xvfb": True,
            "chromium_arg": "--disable-dev-shm-usage"
        }
        
        if proxy_auth:
            sb_args["proxy"] = proxy_auth
            logger.info("Using proxy for Emirates V3 scraper")
        
        with SB(**sb_args) as sb:
            # Track screenshots for debugging
            progress_screenshots = []
            
            def take_screenshot(step_name):
                try:
                    screenshot_dir = "/app/downloaded_files"
                    os.makedirs(screenshot_dir, exist_ok=True)
                    # Use a counter or timestamp to ensure order
                    count = len(progress_screenshots) + 1
                    screenshot_path = f"{screenshot_dir}/emirates_v3_step_{count}_{step_name}_{request.origin}_{request.destination}.png"
                    sb.save_screenshot(screenshot_path)
                    progress_screenshots.append(screenshot_path)
                    logger.info(f"Saved debug screenshot: {screenshot_path}")
                except Exception as e:
                    logger.error(f"Failed to take screenshot for {step_name}: {e}")

            try:
                # Navigate to homepage
                url = "https://www.emirates.com/english/" # Using english to ensure selectors work
                logger.info(f"Opening Emirates homepage: {url}")
                take_screenshot("0_start")
                sb.driver.set_page_load_timeout(60)
                sb.open(url)
                sb.sleep(10)
                take_screenshot("1_loaded_page")
                
                # Handle cookies
                sb.click_if_visible("button#onetrust-accept-btn-handler")
                sb.click_if_visible('button:contains("Accept")')
                sb.click_if_visible('button[aria-label*="Accept"]')
                sb.sleep(3)
                take_screenshot("2_cookies_handled")
                
                # Ensure "Search flights" tab is active
                if sb.is_element_visible('#tab0'):
                    sb.click('#tab0')
                    sb.sleep(2)
                
                # Set origin
                # Selector based on provided HTML: input[name="Departure airport"]
                origin_input = 'input[name="Departure airport"]'
                sb.click(origin_input)
                sb.sleep(1)
                sb.clear(origin_input)
                
                # Type slowly
                for char in request.origin:
                    sb.type(origin_input, char)
                    sb.sleep(0.2)
                sb.sleep(3)
                
                # Wait for dropdown item with matching code
                # Selector: li[data-dropdown-id="LOS"]
                origin_option = f'li[data-dropdown-id="{request.origin}"]'
                if sb.is_element_visible(origin_option):
                    sb.click(origin_option)
                else:
                    logger.warning(f"Origin option {origin_option} not found, clicking first option")
                    sb.click('li[role="option"]:first-child')
                
                sb.sleep(2)
                take_screenshot("3_origin_set")
                
                # Set destination
                # Selector: input[name="Arrival airport"]
                dest_input = 'input[name="Arrival airport"]'
                sb.click(dest_input)
                sb.sleep(1)
                
                # Type slowly
                for char in request.destination:
                    sb.type(dest_input, char)
                    sb.sleep(0.2)
                sb.sleep(3)
                
                # Wait for dropdown item
                dest_option = f'li[data-dropdown-id="{request.destination}"]'
                if sb.is_element_visible(dest_option):
                    sb.click(dest_option)
                else:
                    logger.warning(f"Destination option {dest_option} not found, clicking first option")
                    sb.click('li[role="option"]:first-child')
                
                sb.sleep(2)
                take_screenshot("4_destination_set")
                
                # Set dates
                # Using the robust JS method as it's cleaner than interacting with the complex date picker UI
                dep_date_str = request.departure_date.strftime("%d %b %y")
                ret_date_str = request.return_date.strftime("%d %b %y")
                
                # IDs from provided HTML: search-flight-date-picker--depart, search-flight-date-picker--return
                
                # Set departure date
                sb.click('#search-flight-date-picker--depart')
                sb.sleep(2)
                sb.execute_script(f"""
                    var input = document.querySelector('#search-flight-date-picker--depart');
                    var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                    nativeInputValueSetter.call(input, '{dep_date_str}');
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                """)
                sb.sleep(2)
                
                # Set return date
                sb.click('#search-flight-date-picker--return')
                sb.sleep(2)
                sb.execute_script(f"""
                    var input = document.querySelector('#search-flight-date-picker--return');
                    var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                    nativeInputValueSetter.call(input, '{ret_date_str}');
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                """)
                sb.sleep(3)
                take_screenshot("5_dates_set")
                
                # Search
                # Selector: button.js-widget-submit
                sb.click('button.js-widget-submit')
                sb.sleep(20)
                
            except Exception as e:
                logger.error(f"Failed during form filling: {e}")
                # Debug: Save screenshot and HTML on failure
                try:
                    screenshot_dir = "/app/downloaded_files"
                    os.makedirs(screenshot_dir, exist_ok=True)
                    screenshot_path = f"{screenshot_dir}/emirates_v3_fail_{request.origin}_{request.destination}.png"
                    html_path = f"{screenshot_dir}/emirates_v3_fail_{request.origin}_{request.destination}.html"
                    
                    sb.save_screenshot(screenshot_path)
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(sb.get_page_source())
                    logger.info(f"Debug files saved: {screenshot_path}, {html_path}")
                    
                    raise ScraperError(f"V3 Form filling failed: {e}", screenshot_path, html_path, progress_screenshots)
                except Exception as debug_error:
                    logger.error(f"Failed to save debug files: {debug_error}")
                    raise e

            # Extract results (Reuse logic from V1/V2 or generic extraction)
            # For now, assuming the results page structure is similar to V1
            try:
                logger.info("Waiting for calendar grid element...")
                sb.wait_for_element('.calendar-grid', timeout=60)
                logger.info("Calendar grid found successfully")
            except Exception as e:
                logger.error(f"Failed to find calendar grid: {e}")
                # Debug artifacts
                try:
                    screenshot_dir = "/app/downloaded_files"
                    os.makedirs(screenshot_dir, exist_ok=True)
                    screenshot_path = f"{screenshot_dir}/emirates_v3_calendar_fail_{request.origin}_{request.destination}.png"
                    html_path = f"{screenshot_dir}/emirates_v3_calendar_fail_{request.origin}_{request.destination}.html"
                    sb.save_screenshot(screenshot_path)
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(sb.get_page_source())
                    
                    raise ScraperError(f"Calendar grid not found: {e}", screenshot_path, html_path, progress_screenshots)
                except Exception as debug_error:
                    raise e

            # Parsing logic (Same as V1 for now as the results page is likely the same)
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
