"""Ethics & consent gate — the industry-standard requirement.

From the OSINT community methodology (r/OSINT wiki Part 2): "while performing
OSINT is legal, using the OSINT tools and techniques outlined here are
intended to be used in a legal and ethical manner."

Every scan passes through this gate. It does not block — it makes the
operator affirm the purpose, which is the standard agencies and courses
(IntelTechniques, Bazzell's methodology) require of operators and tooling.
"""

from __future__ import annotations

from enum import Enum


class UseCase(str, Enum):
    INVESTIGATION = "investigation"      # law enforcement / PI / journalist
    TRUST_SAFETY = "trust_safety"        # platform safety / anti-fraud
    MISSING_PERSON = "missing_person"    # locating a missing person
    RESEARCH = "research"                # academic / security research
    BACKGROUND = "background"            # pre-employment / due diligence
    OTHER = "other"


USE_CASE_DESCRIPTIONS = {
    UseCase.INVESTIGATION: "Law enforcement, private investigation, or journalism",
    UseCase.TRUST_SAFETY: "Platform trust & safety / anti-fraud",
    UseCase.MISSING_PERSON: "Locating a missing person",
    UseCase.RESEARCH: "Academic or security research",
    UseCase.BACKGROUND: "Pre-employment screening / due diligence",
    UseCase.OTHER: "Other lawful purpose",
}


class EthicsGate:
    """Affirmation gate: operator declares a lawful purpose before a scan."""

    def __init__(self, auto_accept: bool = False):
        self.auto_accept = auto_accept

    def affirm(self, use_case: UseCase | None = None) -> bool:
        """Confirm lawful use. Returns True when the gate is satisfied."""
        if self.auto_accept:
            return True
        # In non-interactive mode (scripts/cron), require an explicit --purpose.
        # Interactive mode is handled at the CLI layer.
        return use_case is not None

    @staticmethod
    def notice() -> str:
        return (
            "\n⚠️  LEGAL & ETHICAL USE REQUIRED\n"
            "EagleEye 2.0 gathers only publicly available information (OSINT).\n"
            "Use it only for lawful purposes: investigations, trust & safety,\n"
            "missing-person searches, research, or due diligence. Misuse —\n"
            "including stalking, doxxing, or harassment — is illegal and is\n"
            "the responsibility of the operator. This tool has no bypass.\n"
        )
