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

# Geonode Scraper API - proxy + extraction ek endpoint mein. Agar .env mein
# GEONODE_API_KEY set ho, isay use karte hain (websites jo direct request
# block kar dete hain, unke liye zyada reliable). Key na ho to system
# khud direct request pe fallback kar jata hai - koi crash nahi hota.
GEONODE_API_KEY = os.getenv("GEONODE_API_KEY")
GEONODE_SCRAPER_URL = "https://api.geonode.com/v1/scraper"

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
        false-positive block ho jaati hain (common cause: firewalls unusual
        bot User-Agents ko robots.txt request pe hi reject kar dete hain).
        """
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            resp = requests.get(robots_url, headers=HEADERS, timeout=5)

            # robots.txt maujood nahi (404) ya server ne request hi reject kar di
            # -> ye "disallow" nahi hai, isliye allow maante hain
            if resp.status_code != 200:
                return True

            rp = urllib.robotparser.RobotFileParser()
            rp.parse(resp.text.splitlines())
            return rp.can_fetch(HEADERS["User-Agent"], url)

        except Exception:
            # Network error, timeout, etc. - fail-safe: allow karte hain
            return True

    def _extract_emails_from_html(self, html: str) -> list[str]:
        """Page ke text aur mailto: links dono se email nikalta hai."""
        emails = set()

        soup = BeautifulSoup(html, "html.parser")

        # mailto: links (sabse reliable source)
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("mailto:"):
                email = href.replace("mailto:", "").split("?")[0].strip()
                emails.add(email)

        # Plain text mein regex se dhoondo (footer, contact section, etc.)
        text = soup.get_text(" ")
        for match in EMAIL_REGEX.findall(text):
            emails.add(match)

        # Junk/fake emails filter out karo
        clean_emails = [
            e for e in emails
            if not any(junk in e.lower() for junk in JUNK_PATTERNS)
        ]

        return clean_emails

    def _fetch_via_geonode(self, url: str) -> str | None:
        """Geonode Scraper API se page fetch karta hai (proxy + extraction ek sath)."""
        if not GEONODE_API_KEY:
            return None
        try:
            resp = requests.post(
                GEONODE_SCRAPER_URL,
                headers={"Authorization": f"Bearer {GEONODE_API_KEY}"},
                json={"url": url},
                timeout=self.timeout + 10,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            # Geonode response mein content alag keys ke neeche aa sakta hai -
            # jo bhi mile wahi use karte hain
            for key in ("html", "content", "markdown", "text"):
                if data.get(key):
                    return data[key]
            return None
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

        # URL normalize karo (https:// missing ho to add karo)
        if not website_url.startswith(("http://", "https://")):
            website_url = "https://" + website_url

        if self.respect_robots and not self._is_allowed_by_robots(website_url):
            result.error_reason = "blocked_by_robots_txt"
            return result

        # Step 1: Homepage check
        html = self._fetch_page(website_url)
        if html is None:
            result.error_reason = "website_unreachable"
            result.website_live = False
            return result

        result.website_live = True
        result.pages_checked.append(website_url)

        emails = self._extract_emails_from_html(html)

        # Step 2: Agar homepage pe email nahi mila, contact pages try karo
        if not emails:
            parsed = urlparse(website_url)
            base = f"{parsed.scheme}://{parsed.netloc}"

            for path in CONTACT_PATHS:
                if emails:
                    break
                time.sleep(0.5)  # respectful rate limiting
                contact_url = urljoin(base, path)
                contact_html = self._fetch_page(contact_url)
                if contact_html:
                    result.pages_checked.append(contact_url)
                    emails = self._extract_emails_from_html(contact_html)

        if emails:
            result.email = emails[0]  # pehla valid email use karo
            result.email_found = True
        else:
            result.error_reason = "no_email_found"

        return result
