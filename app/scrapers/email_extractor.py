"""
Email Scraper - business ke website se contact email nikalta hai.

Kahan dhoondta hai (client brief ke mutabiq):
1. Homepage
2. Common contact pages (/contact, /contact-us, /about, /about-us)
3. Footer (agar homepage pe hi ho to)

Failure handling (zaroori hai - client brief ka requirement):
- Website down / timeout       -> crash nahi hota, ScrapeResult.error_reason set hota hai
- Website hai lekin email nahi -> email_found=False, pipeline aage badhta rehta hai
- robots.txt disallow karta ho -> scrape skip, respectful rehte hain
"""

import os
import re
import time
import urllib.robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapeResult

HEADERS = {
    "User-Agent": "LocalLeadGenPlatform/1.0 (internship-project; respectful-crawler)"
}

# Geonode Scraper API - proxy + extraction ek endpoint mein (docs.geonode.com).
# Agar .env mein GEONODE_API_KEY set ho, isay use karte hain (websites jo
# direct request block kar dete hain, unke liye zyada reliable). Key na ho
# to system khud direct request pe fallback kar jata hai - koi crash nahi.
GEONODE_API_KEY = os.getenv("GEONODE_API_KEY")
GEONODE_EXTRACT_URL = "https://scraper.geonode.io/v1/extract"

# Common contact page paths jo try karte hain agar homepage pe email na mile
CONTACT_PATHS = ["/contact", "/contact-us", "/contact.html", "/about", "/about-us"]

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# In domains/patterns se aane wale "emails" fake/junk hote hain - inhe ignore karte hain
JUNK_PATTERNS = [
    "example.com", "yourdomain.com", "sentry.io", "wixpress.com",
    "godaddy.com", "domain.com", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    "schema.org", "w3.org",
]


class EmailScraper(BaseScraper):

    def __init__(self, timeout: int = 10, respect_robots: bool = True):
        self.timeout = timeout
        self.respect_robots = respect_robots

    def _is_allowed_by_robots(self, url: str) -> bool:
        """
        robots.txt check karta hai - lekin sirf jab explicitly "Disallow" mile.
        Agar robots.txt fetch hi na ho paaye (404, firewall block, timeout, etc.)
        to default ALLOW maante hain - warna bohat si genuine websites
        false-positive block ho jaati hain.
        """
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            resp = requests.get(robots_url, headers=HEADERS, timeout=5)

            if resp.status_code != 200:
                return True

            rp = urllib.robotparser.RobotFileParser()
            rp.parse(resp.text.splitlines())
            return rp.can_fetch(HEADERS["User-Agent"], url)

        except Exception:
            return True

    def _extract_emails_from_html(self, html: str) -> list[str]:
        """Page ke text aur mailto: links dono se email nikalta hai."""
        emails = set()

        soup = BeautifulSoup(html, "html.parser")

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("mailto:"):
                email = href.replace("mailto:", "").split("?")[0].strip()
                emails.add(email)

        text = soup.get_text(" ")
        for match in EMAIL_REGEX.findall(text):
            emails.add(match)

        clean_emails = [
            e for e in emails
            if not any(junk in e.lower() for junk in JUNK_PATTERNS)
        ]

        return clean_emails

    def _fetch_via_geonode(self, url: str) -> str | None:
        """
        Geonode Extraction API se page fetch karta hai (proxy + rendering
        ek sath handle hota hai). Response format (docs.geonode.com ke
        mutabiq):
            { "data": { "html": "...", "markdown": "..." }, "metadata": {...} }
        """
        if not GEONODE_API_KEY:
            return None
        try:
            resp = requests.post(
                GEONODE_EXTRACT_URL,
                headers={
                    "X-Api-Key": GEONODE_API_KEY,
                    "Content-Type": "application/json",
                },
                json={"url": url, "formats": ["html"]},
                timeout=self.timeout + 15,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            html = data.get("data", {}).get("html")
            return html if html else None
        except (requests.RequestException, ValueError):
            return None

    def _fetch_page(self, url: str) -> str | None:
        # Pehle Geonode try karte hain (agar configured ho) - proxy ke zariye
        # blocked/protected sites bhi milne ka chance zyada hota hai
        geonode_result = self._fetch_via_geonode(url)
        if geonode_result:
            return geonode_result

        # Geonode na ho ya fail ho jaye, direct request pe fallback
        try:
            resp = requests.get(url, headers=HEADERS, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.text
        except requests.RequestException:
            return None
        return None

    def scrape(self, website_url: str) -> ScrapeResult:
        result = ScrapeResult(website_url=website_url)

        if not website_url:
            result.error_reason = "no_website"
            return result

        if not website_url.startswith(("http://", "https://")):
            website_url = "https://" + website_url

        if self.respect_robots and not self._is_allowed_by_robots(website_url):
            result.error_reason = "blocked_by_robots_txt"
            return result

        html = self._fetch_page(website_url)
        if html is None:
            result.error_reason = "website_unreachable"
            result.website_live = False
            return result

        result.website_live = True
        result.pages_checked.append(website_url)

        emails = self._extract_emails_from_html(html)

        if not emails:
            parsed = urlparse(website_url)
            base = f"{parsed.scheme}://{parsed.netloc}"

            for path in CONTACT_PATHS:
                if emails:
                    break
                time.sleep(0.5)
                contact_url = urljoin(base, path)
                contact_html = self._fetch_page(contact_url)
                if contact_html:
                    result.pages_checked.append(contact_url)
                    emails = self._extract_emails_from_html(contact_html)

        if emails:
            result.email = emails[0]
            result.email_found = True
        else:
            result.error_reason = "no_email_found"

        return result
