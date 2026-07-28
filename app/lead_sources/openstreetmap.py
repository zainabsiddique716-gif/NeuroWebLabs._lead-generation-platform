"""
OpenStreetMap Lead Source - 100% FREE, no API key required.

Do free public APIs use hoti hain:
1. Nominatim  -> location (e.g. "Lahore, Pakistan") ko bounding box
                 coordinates mein convert karta hai (geocoding)
2. Overpass   -> us bounding box ke andar business/POI data
                 (name, address, phone, website, lat/lon) deta hai

Rate limit: Nominatim policy ke mutabiq max 1 request/second -
isliye humne time.sleep() lagaya hai. Ye production mein bhi safe hai.
"""

import time
import requests
from .base import BaseLeadSource, BusinessResult

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Multiple mirrors - agar ek server busy/timeout ho to agla try karta hai.
# Ye Overpass ka free public infrastructure hai, isliye occasional
# overload hona normal hai - retry logic isay handle karta hai.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

# Free-text query ko OSM tags mein map karta hai.
# Naya category add karna ho to bas yahan ek entry add karein.
CATEGORY_MAP = {
    "dentist": ("amenity", "dentist"),
    "dentists": ("amenity", "dentist"),
    "gym": ("leisure", "fitness_centre"),
    "gyms": ("leisure", "fitness_centre"),
    "restaurant": ("amenity", "restaurant"),
    "restaurants": ("amenity", "restaurant"),
    "cafe": ("amenity", "cafe"),
    "cafes": ("amenity", "cafe"),
    "salon": ("shop", "hairdresser"),
    "salons": ("shop", "hairdresser"),
    "pharmacy": ("amenity", "pharmacy"),
    "pharmacies": ("amenity", "pharmacy"),
    "hospital": ("amenity", "hospital"),
    "hospitals": ("amenity", "hospital"),
    "school": ("amenity", "school"),
    "schools": ("amenity", "school"),
    "hotel": ("tourism", "hotel"),
    "hotels": ("tourism", "hotel"),
    "clinic": ("amenity", "clinic"),
    "clinics": ("amenity", "clinic"),
    "bakery": ("shop", "bakery"),
    "bakeries": ("shop", "bakery"),
}

HEADERS = {
    # Nominatim policy requires a real User-Agent identifying the app
    "User-Agent": "LocalLeadGenPlatform/1.0 (internship-project)"
}


class OpenStreetMapSource(BaseLeadSource):

    def _geocode_location(self, location: str) -> tuple[float, float, float, float]:
        """Location string ko bounding box (south, north, west, east) mein convert karta hai."""
        params = {"q": location, "format": "json", "limit": 1}
        resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        results = resp.json()
        if not results:
            raise ValueError(f"Location not found: {location}")

        bbox = results[0]["boundingbox"]  # [south, north, west, east] as strings
        return float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])

    def _guess_tag(self, query: str) -> tuple[str, str]:
        """Free-text query se OSM tag guess karta hai. Match na mile to generic shop tag use hota hai."""
        key = query.strip().lower()
        if key in CATEGORY_MAP:
            return CATEGORY_MAP[key]
        # partial match try karo
        for k, v in CATEGORY_MAP.items():
            if k in key or key in k:
                return v
        # fallback: generic name-based search
        return ("name", None)

    def search(self, query: str, location: str, limit: int = 20) -> list[BusinessResult]:
        south, north, west, east = self._geocode_location(location)
        time.sleep(1)  # Nominatim rate limit respect karna zaroori hai

        tag_key, tag_value = self._guess_tag(query)

        if tag_value:
            tag_filter = f'["{tag_key}"="{tag_value}"]'
        else:
            # tag guess nahi hua to naam mein query dhoondo
            tag_filter = f'["name"~"{query}",i]'

        overpass_query = f"""
        [out:json][timeout:25];
        (
          node{tag_filter}({south},{west},{north},{east});
          way{tag_filter}({south},{west},{north},{east});
        );
        out center {limit};
        """

        # Har mirror try karte hain - agar ek timeout/fail ho to agla try
        data = None
        last_error = None
        for overpass_url in OVERPASS_URLS:
            try:
                resp = requests.post(overpass_url, data={"data": overpass_query}, headers=HEADERS, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                break  # success - loop se bahar nikal jao
            except Exception as e:
                last_error = e
                continue  # is mirror ne fail kiya, agla try karo

        if data is None:
            raise ValueError(f"All Overpass servers busy/unreachable right now, try again in a bit ({last_error})")

        results = []
        for el in data.get("elements", [])[:limit]:
            tags = el.get("tags", {})

            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")

            address_parts = [
                tags.get("addr:housenumber", ""),
                tags.get("addr:street", ""),
                tags.get("addr:city", ""),
            ]
            address = ", ".join([p for p in address_parts if p]) or tags.get("addr:full", "")

            results.append(BusinessResult(
                name=tags.get("name", "Unknown Business"),
                category=tag_value or query,
                address=address or None,
                phone=tags.get("contact:phone") or tags.get("phone"),
                rating=None,  # OSM me rating field nahi hoti
                website_url=tags.get("contact:website") or tags.get("website"),
                latitude=lat,
                longitude=lon,
                source="openstreetmap",
                raw_data=tags,
            ))

        return results
