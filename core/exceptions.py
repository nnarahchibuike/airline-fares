"""Custom exceptions for the scraper."""

class ScraperError(Exception):
    """Exception raised when a scraper fails with debug artifacts."""
    
    def __init__(self, message: str, screenshot_path: str = None, html_path: str = None, screenshot_paths: list = None):
        """
        Initialize ScraperError.
        
        Args:
            message: Error message
            screenshot_path: Path to the final failure screenshot
            html_path: Path to the debug HTML dump
            screenshot_paths: List of paths to screenshots taken during execution
        """
        super().__init__(message)
        self.screenshot_path = screenshot_path
        self.html_path = html_path
        self.screenshot_paths = screenshot_paths or []
        if screenshot_path and screenshot_path not in self.screenshot_paths:
            self.screenshot_paths.append(screenshot_path)
