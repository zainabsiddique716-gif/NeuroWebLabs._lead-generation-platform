"""
Abstract base for Qualification Rules.

Har rule ek chhota class hai jo lead ko check karta hai aur
(passed: bool, reason: str) return karta hai. Naya rule add
karna ho to bas ek nayi class banayein aur QUALIFICATION_RULES
list (rules.py mein) mein add kar dein - kahin aur code touch
nahi karna parega.
"""

from abc import ABC, abstractmethod


class BaseRule(ABC):
    name: str = "base_rule"

    @abstractmethod
    def check(self, business: dict, lead: dict) -> tuple[bool, str]:
        """
        business: business ka dict (name, website_url, rating, etc.)
        lead: lead ka dict (email, email_found, website_live, etc.)

        Returns: (passed, reason) - passed=False ho to reason batata
        hai kyun reject hua.
        """
        raise NotImplementedError
