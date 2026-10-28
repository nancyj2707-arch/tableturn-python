"""Request and response models. Every response goes through one of these; bodies use Field constraints.
Optional fields are left out of the answer when they have no value (the routes serialise with exclude_none), so a free
table carries no party and a waiting party no table."""
from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, Field, PlainSerializer

Section = Literal["Window", "Garden", "Indoor"]
TableState = Literal["free", "seated", "uncleared"]
PartyState = Literal["waiting", "seated", "left", "cleared"]


def _iso_z(dt: datetime) -> str:
    """SQLite hands naive datetimes back; everything the app stores is UTC, so a naive value is UTC, never local time."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


UtcZ = Annotated[datetime, PlainSerializer(_iso_z, return_type=str)]


class TableOut(BaseModel):
    no: str
    seats: int
    section: Section
    state: TableState
    party_id: str | None = None          # seated and uncleared tables: whose table it is
    seating_id: str | None = None        # seated and uncleared tables
    seated_minutes: int | None = None    # seated tables only


class FloorOut(BaseModel):
    branch: str
    free: int
    tables: list[TableOut]


class JoinIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    covers: int = Field(ge=1, le=20)
    phone: str | None = Field(default=None, pattern=r"^\+[1-9]\d{7,14}$", description="E.164, optional")


class JoinOut(BaseModel):
    party_id: str
    name: str
    covers: int
    position: int
    joined_at: UtcZ


class PartyOut(BaseModel):
    party_id: str
    name: str
    covers: int
    state: PartyState
    position: int
    joined_at: UtcZ