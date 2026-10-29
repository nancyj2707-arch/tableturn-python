"""Public ids are opaque strings (W031, S204, T09); database integers never reach the wire."""
import re

_PARTY = re.compile(r"^W(\d{3,})$")


def party_public(internal_id: int) -> str:
    return f"W{internal_id:03d}"


def party_internal(public_id: str) -> int | None:
    m = _PARTY.match(public_id or "")
    return int(m.group(1)) if m else None


def seating_public(internal_id: int) -> str:
    return f"S{internal_id:03d}"