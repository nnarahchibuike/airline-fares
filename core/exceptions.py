"""Custom exceptions for the scraper."""

class ScraperError(Exception):
    """Exception raised when a scraper fails with debug artifacts."""
    
    def __init__(self, message: str, screenshot_path: str = None, html_path: str = None):
        """
        Initialize ScraperError.
        
        Args:
            message: Error message
            screenshot_path: Path to the debug screenshot
            html_path: Path to the debug HTML dump
        """
        super().__init__(message)
        self.screenshot_path = screenshot_path
        self.html_path = html_path
