"""Data models for flight scraping system."""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List


@dataclass
class FlightRequest:
    """Request parameters for flight search."""
    origin: str          # Airport code, e.g., "LOS"
    destination: str     # Airport code, e.g., "CAN"
    departure_date: date
    return_date: date
    adults: int = 1
    
    def __post_init__(self):
        """Validate request parameters."""
        if not self.origin or not self.destination:
            raise ValueError("Origin and destination are required")
        if self.departure_date >= self.return_date:
            raise ValueError("Return date must be after departure date")
        if self.adults < 1:
            raise ValueError("At least 1 adult passenger required")


@dataclass
class FlightResult:
    """Result from flight scraping."""
    airline: str
    origin: str
    destination: str
    departure_date: str   # e.g., "Dec 3"
    return_date: str      # e.g., "Dec 23"
    price: float          # Numeric price for sorting
    currency: str         # e.g., "NGN", "USD"
    price_display: str    # e.g., "NGN 2,592,377"
    is_lowest: bool = False
    screenshot_paths: List[str] = field(default_factory=list)
    
    def __str__(self):
        """String representation for display."""
        lowest_tag = " ⭐ LOWEST" if self.is_lowest else ""
        return f"{self.airline}: {self.price_display}{lowest_tag}"
