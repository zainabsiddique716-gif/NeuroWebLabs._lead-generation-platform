"""
Abstract base for Outreach Channels.

Abhi EmailChannel hai (SMTP se email bhejta hai). Kal agar
WhatsApp ya LinkedIn outreach add karna ho, to bas BaseChannel
ko inherit kar ke naya module bana lein.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SendResult:
    success: bool
    status: str              # "sent" / "dry_run" / "failed"
    error_message: Optional[str] = None


class BaseChannel(ABC):

    @abstractmethod
    def send(self, to_email: str, subject: str, body: str) -> SendResult:
        raise NotImplementedError
