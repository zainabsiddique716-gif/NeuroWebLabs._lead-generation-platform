"""
Abstract base class for all Lead Source modules.

Har naya lead source (OpenStreetMap, Google Places, LinkedIn, etc.)
is interface ko implement karega. Pipeline kabhi ye nahi jaanta ke
data kahan se aa raha hai - bas .search() call karta hai.

Naya source add karna ho to sirf ek nayi file banayein jo
BaseLeadSource ko inherit kare - kahin aur code change nahi karna.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BusinessResult:
    """Ek business ka standardized structure - chahe data kisi bhi source se aaye."""
    name: str
    category: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    rating: Optional[float] = None
    website_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: str = "unknown"
    raw_data: dict = field(default_factory=dict)


class BaseLeadSource(ABC):
    """
    Har lead source class ko ye method implement karna hoga.

    Example:
        source = OpenStreetMapSource()
        results = source.search(query="dentists", location="Lahore, Pakistan")
    """

    @abstractmethod
    def search(self, query: str, location: str, limit: int = 20) -> list[BusinessResult]:
        raise NotImplementedError
