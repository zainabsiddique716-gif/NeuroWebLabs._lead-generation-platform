"""
Abstract base class for all Website Scraper modules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScrapeResult:
    website_url: str
    email: Optional[str] = None
    email_found: bool = False
    website_live: bool = False
    error_reason: Optional[str] = None
    pages_checked: list = field(default_factory=list)


class BaseScraper(ABC):
    @abstractmethod
    def scrape(self, website_url: str) -> ScrapeResult:
        raise NotImplementedError
