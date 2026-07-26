"""
Qualification Rules - client brief ke Section 4.3 ke mutabiq.

Ye rules yahan easily adjustable hain - MIN_RATING badalna ho ya
koi rule on/off karna ho, bas neeche ke values/list change karein.
Kahin bhi hardcoded deep in the logic nahi hai.
"""

from .base import BaseRule

# ---- Easily adjustable settings ----
MIN_RATING = 3.5   # rating null ho (OSM mein aksar hoti hai) to ye rule skip ho jata hai


class HasEmailRule(BaseRule):
    name = "has_email"

    def check(self, business: dict, lead: dict) -> tuple[bool, str]:
        if lead.get("email_found"):
            return True, "email present"
        return False, "no email found"


class WebsiteLiveRule(BaseRule):
    name = "website_live"

    def check(self, business: dict, lead: dict) -> tuple[bool, str]:
        if not business.get("website_url"):
            return False, "no website listed"
        if lead.get("website_live") is False:
            return False, "website unreachable"
        return True, "website ok"


class MinRatingRule(BaseRule):
    name = "min_rating"

    def check(self, business: dict, lead: dict) -> tuple[bool, str]:
        rating = business.get("rating")
        if rating is None:
            return True, "rating not available - skipped"  # OSM data mein rating aksar nahi hoti
        if rating < MIN_RATING:
            return False, f"rating {rating} below minimum {MIN_RATING}"
        return True, "rating ok"


# Yahan naye rules add/remove karke qualification criteria adjust karein
QUALIFICATION_RULES: list[BaseRule] = [
    HasEmailRule(),
    WebsiteLiveRule(),
    MinRatingRule(),
]


def run_qualification(business: dict, lead: dict) -> tuple[str, str | None]:
    """
    Saare rules chalata hai. Koi bhi rule fail ho to lead 'rejected'
    hota hai us reason ke saath. Sab pass ho to 'qualified'.

    Returns: (status, rejection_reason)
    """
    for rule in QUALIFICATION_RULES:
        passed, reason = rule.check(business, lead)
        if not passed:
            return "rejected", f"{rule.name}: {reason}"

    return "qualified", None
