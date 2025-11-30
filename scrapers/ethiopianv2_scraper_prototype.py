"""Ethiopian V2 Scraper Prototype."""
from typing import List
import logging
import os
import time
from seleniumbase import SB
from bs4 import BeautifulSoup

from scrapers.base_scraper import AirlineScraper
from core.models import FlightRequest, FlightResult

# Set up logger
logger = logging.getLogger(__name__)

class EthiopianV2ScraperPrototype(AirlineScraper):
    """Prototype scraper for Ethiopian Airlines using UI interaction."""
    
    def __init__(self):
        """Initialize EthiopianV2 scraper."""
        super().__init__("EthiopianV2Prototype")
    
    def scrape(self, request: FlightRequest) -> List[FlightResult]:
        """
        Scrape Ethiopian Airlines using UI interaction.
        
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
            "ad_block": False, # Sometimes adblock breaks site functionality
            "xvfb": True,
            "chromium_arg": [
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-webrtc",
                "--disable-blink-features=AutomationControlled"
            ]
        }
        
        if proxy_auth:
            sb_args["proxy"] = proxy_auth
            logger.info("Using proxy for Ethiopian V2 scraper")
        
        with SB(**sb_args) as sb:
            # Track screenshots for debugging
            progress_screenshots = []
            
            def take_screenshot(step_name):
                try:
                    screenshot_dir = os.path.join(os.getcwd(), "downloaded_files")
                    os.makedirs(screenshot_dir, exist_ok=True)
                    # Use a counter to ensure order
                    count = len(progress_screenshots) + 1
                    screenshot_path = f"{screenshot_dir}/ethiopianv2_step_{count}_{step_name}.png"
                    sb.save_screenshot(screenshot_path)
                    progress_screenshots.append(screenshot_path)
                    logger.info(f"Saved debug screenshot: {screenshot_path}")
                except Exception as e:
                    logger.error(f"Failed to take screenshot for {step_name}: {e}")

            try:
                # 1. Navigation
                url = "https://www.ethiopianairlines.com/book/booking/flight"
                logger.info(f"Opening Ethiopian booking page: {url}")
                take_screenshot("0_start")
                sb.open(url)
                sb.sleep(10) # Wait for page load
                take_screenshot("1_loaded_page")
                
                # Handle cookies if present
                sb.click_if_visible("button#onetrust-accept-btn-handler")
                sb.click_if_visible('button:contains("Accept")')
                sb.sleep(2)
                
                # 2. Origin - Hardcoded to Lagos
                logger.info("Setting Origin to Lagos via JS")
                
                js_origin = """
                    document.getElementById('origin-input-hidden').value = 'LOS';
                    // Trigger events
                    var input = document.getElementById('origin-input-hidden');
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                    
                    // Update display
                    var code = document.querySelector('.origin-airport-code');
                    if(code) code.innerText = ' | LOS';
                    var name = document.querySelector('.origin-airport-name');
                    if(name) name.innerText = 'Lagos';
                    
                    // Hide placeholder, show text
                    document.querySelector('.widget-origin-placeholder-text').style.display = 'none';
                """
                sb.execute_script(js_origin)
                sb.sleep(1)
                take_screenshot("2_origin_set")
                
                # 3. Destination - Hardcoded to Guangzhou
                logger.info("Setting Destination to Guangzhou via JS")
                
                js_dest = """
                    document.getElementById('destination-input-hidden').value = 'CAN';
                    // Trigger events
                    var input = document.getElementById('destination-input-hidden');
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                    
                    // Update display
                    var code = document.querySelector('.destination-airport-code');
                    if(code) code.innerText = ' | CAN';
                    var name = document.querySelector('.destination-airport-name');
                    if(name) name.innerText = 'Guangzhou';
                    
                    // Hide placeholder, show text
                    document.querySelector('.widget-destination-placeholder-text').style.display = 'none';
                """
                sb.execute_script(js_dest)
                sb.sleep(1)
                take_screenshot("3_destination_set")
                
                # 4. Dates - Hardcoded via JS
                logger.info("Setting Dates via JS")
                dep_date = "2026-01-04"
                ret_date = "2026-01-21"
                
                # Set hidden inputs
                js_script = f"""
                    // Set hidden inputs
                    document.getElementById('flatpickr-departure-date-hidden').value = '{dep_date}';
                    document.getElementById('flatpickr-return-date-hidden').value = '{ret_date}';
                    document.getElementById('departure-date-hidden').value = '{dep_date}';
                    document.getElementById('return-date-hidden').value = '{ret_date}';
                    
                    // Update display
                    var depContainer = document.getElementById('inner-departure-date');
                    if(depContainer) {{
                        depContainer.innerHTML = '<span class="day pop-date-stay d-inline">04</span>/<span class="month pop-date-stay d-inline">01</span>/<span class="year pop-date-stay d-inline">2026</span>';
                    }}
                    
                    var retContainer = document.getElementById('inner-return-date');
                    if(retContainer) {{
                        retContainer.innerHTML = '<span class="day pop-date-stay d-inline">21</span>/<span class="month pop-date-stay d-inline">01</span>/<span class="year pop-date-stay d-inline">2026</span>';
                    }}
                """
                sb.execute_script(js_script)
                sb.sleep(2)
                take_screenshot("4_dates_set")
                
                # 5. Search
                logger.info("Clicking Search")
                search_selector = "#advanced-search-flight"
                sb.wait_for_element(search_selector)
                sb.click(search_selector)
                
                sb.sleep(5)
                take_screenshot("5_search_clicked")
                
                # 6. Wait for URL change and modify to matrix
                logger.info("Waiting for URL to contain 'flight-selection'...")
                try:
                    sb.wait_for_element("body", timeout=60) # Wait for page load
                    
                    # Wait loop for URL change
                    max_retries = 20
                    for _ in range(max_retries):
                        current_url = sb.get_current_url()
                        if "flight-selection" in current_url:
                            logger.info(f"Captured URL: {current_url}")
                            break
                        sb.sleep(1)
                    else:
                        logger.warning("URL did not change to flight-selection within timeout")
                    
                    # Modify URL
                    current_url = sb.get_current_url()
                    if "flight-selection" in current_url:
                        new_url = current_url.replace("flight-selection", "matrix")
                        logger.info(f"Navigating to Matrix URL: {new_url}")
                        sb.open(new_url)
                        sb.sleep(5) # Wait for initial load
                        
                        logger.info("Reloading page as requested...")
                        sb.refresh()
                        
                        logger.info("Waiting 30 seconds for page to fully load...")
                        sb.sleep(30)
                        
                        take_screenshot("6_matrix_reloaded")
                    
                    # 7. Wait for results (Matrix)
                    logger.info("Waiting for matrix results...")
                    sb.wait_for_element(".dxp-matrix-grid-layout", timeout=60)
                    take_screenshot("7_matrix_loaded")
                    
                    # Save HTML for inspection
                    html_path = os.path.join(os.getcwd(), "downloaded_files", "ethiopianv2_results.html")
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(sb.get_page_source())
                    logger.info(f"Saved results HTML to {html_path}")
                    
                    # 8. Parse Results
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(sb.get_page_source(), 'html.parser')
                    table = soup.find('table', class_='dxp-matrix-grid-layout')
                    
                    parsed_results = []
                    if table:
                        # Get Departure Dates (Columns)
                        dep_dates = []
                        header_cells = table.select('thead th.date-header')
                        for th in header_cells:
                            date_div = th.find('div', class_='number')
                            if date_div:
                                dep_dates.append(date_div.get_text(strip=True))
                        
                        logger.info(f"Found {len(dep_dates)} departure dates columns")
                        
                        # Iterate Rows (Return Dates)
                        rows = table.select('tbody tr')
                        for row in rows:
                            # Get Return Date (Last cell in row is th)
                            ret_header = row.select_one('th.date-header')
                            if not ret_header:
                                continue
                            ret_date_div = ret_header.find('div', class_='number')
                            if not ret_date_div:
                                continue
                            ret_date = ret_date_div.get_text(strip=True)
                            
                            # Get Prices (Cells)
                            cells = row.select('td.dxp-matrix-cell')
                            for i, cell in enumerate(cells):
                                if i >= len(dep_dates):
                                    break
                                    
                                price_span = cell.select_one('.number')
                                if price_span:
                                    price_text = price_span.get_text(strip=True)
                                    currency_span = cell.select_one('.currency')
                                    currency = currency_span.get_text(strip=True) if currency_span else "NGN"
                                    
                                    parsed_results.append({
                                        "departure_date": dep_dates[i],
                                        "return_date": ret_date,
                                        "price": price_text,
                                        "currency": currency
                                    })
                        
                        logger.info(f"Successfully parsed {len(parsed_results)} flight options")
                        for res in parsed_results[:5]: # Log first 5
                            logger.info(f"Sample Result: {res}")
                            
                        # Convert to FlightResult objects
                        for res in parsed_results:
                            results.append(FlightResult(
                                airline="Ethiopian",
                                origin=request.origin,
                                destination=request.destination,
                                departure_date=res["departure_date"], # Note: This is just "Jan 01", needs year handling ideally but for prototype OK
                                return_date=res["return_date"],
                                price=float(res["price"].replace(",", "")),
                                price_display=f"{res['currency']} {res['price']}",
                                currency=res["currency"]
                            ))
                            
                    else:
                        logger.error("Matrix table not found in HTML source")

                except Exception as e:
                    logger.error(f"Error during URL modification or matrix load: {e}")
                    take_screenshot("error_matrix")
                    # Save HTML even on error
                    html_path = os.path.join(os.getcwd(), "downloaded_files", "ethiopianv2_error.html")
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(sb.get_page_source())
                    raise e

            except Exception as e:
                logger.error(f"Error during Ethiopian V2 scrape: {e}")
                take_screenshot("error")
                raise e
                
        return results
