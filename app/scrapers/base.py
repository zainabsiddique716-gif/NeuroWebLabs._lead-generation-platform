"""
Abstract base class for all Website Scraper modules.

Abhi humare paas EmailScraper hai (contact email dhoondta hai).
Kal agar koi aur scraper add karna ho (e.g. social media links
scrape karna, ya business hours nikalna), to bas BaseScraper ko
inherit kar ke naya module bana lein - pipeline ka baaqi code
touch nahi karna parega.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScrapeResult:
    """Website scrape karne ka result - success ho ya fail, dono cases handle karta hai."""
    website_url: str
    email: Optional[str] = None
    email_found: bool = False
    website_live: bool = False
    error_reason: Optional[str] = None   # e.g. "timeout", "no_email_found", "connection_error"
    pages_checked: list = field(default_factory=list)


class BaseScraper(ABC):
    """
    Har scraper class ko ye method implement karna hoga.

    Example:
        scraper = EmailScraper()
        result = scraper.scrape(website_url="https://example.com")
    """

    @abstractmethod
    def scrape(self, website_url: str) -> ScrapeResult:
        raise NotImplementedError
