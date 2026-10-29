"""Seat a party, let it leave, clear the table. Every refusal is raised here, never in a route; every
change is one transaction."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..clock import Clock, minutes_between
from ..errors import (
    AlreadyCleared,
    AlreadyLeft,
    AlreadySeated,
    NoSuchParty,
    NoSuchSeating,
    NoSuchTable,
    NotLeftYet,
    TableNotCleared,
    TableTooSmall,
)
from ..ids import party_internal, party_public, seating_internal
from ..models import Branch, DiningTable, Party, Seating


def _party(session: Session, branch: Branch, public_id: str) -> Party:
    internal = party_internal(public_id)
    party = session.get(Party, internal) if internal is not None else None
    if party is None or party.branch_id != branch.id:
        raise NoSuchParty(f"There is no party {public_id!r} on the {branch.code} list")
    return party


def _table(session: Session, branch: Branch, no: str) -> DiningTable:
    table = session.scalar(select(DiningTable).where(DiningTable.branch_id == branch.id, DiningTable.no == no))
    if table is None:
        raise NoSuchTable(f"There is no table {no!r} in branch {branch.code}")
    return table


def _seating(session: Session, branch: Branch, public_id: str) -> Seating:
    internal = seating_internal(public_id)
    seating = session.get(Seating, internal) if internal is not None else None
    if seating is None or seating.branch_id != branch.id:
        raise NoSuchSeating(f"There is no seating {public_id!r}")
    return seating


def seat(session: Session, branch: Branch, party_public_id: str, table_no: str, clock: Clock) -> Seating:
    # The order of checks is fixed so that a test can target each refusal — party, table, already seated,
    # cleared, fits.
    party = _party(session, branch, party_public_id)
    table = _table(session, branch, table_no)
    if party.state != "waiting":
        raise AlreadySeated(f"{party_public(party.id)} is already seated (state {party.state})")
    if table.current_seating_id is not None:
        current = session.get(Seating, table.current_seating_id)
        if current.left_at is None:
            raise TableNotCleared(f"{table.no} is occupied by {party_public(current.party_id)}")
        raise TableNotCleared(f"{table.no} has not been cleared since {party_public(current.party_id)} left")
    if table.seats < party.covers:
        raise TableTooSmall(f"{table.no} seats {table.seats}; the party has {party.covers} covers")

    now = clock.now()
    seating = Seating(branch_id=branch.id, party_id=party.id, table_id=table.id, seated_at=now)
    session.add(seating)
    session.flush()
    table.current_seating_id = seating.id
    party.state = "seated"
    party.waited_minutes = minutes_between(party.joined_at, now)      # stamped once, never recomputed
    session.commit()
    return seating


def leave(session: Session, branch: Branch, seating_public_id: str, clock: Clock) -> Seating:
    seating = _seating(session, branch, seating_public_id)
    if seating.left_at is not None:
        raise AlreadyLeft(f"{seating_public_id} left at {seating.left_at:%H:%M}")
    now = clock.now()
    seating.left_at = now
    party = session.get(Party, seating.party_id)
    party.state = "left"
    session.commit()
    return seating


def clear(session: Session, branch: Branch, seating_public_id: str, clock: Clock) -> tuple[Seating, DiningTable]:
    seating = _seating(session, branch, seating_public_id)
    if seating.left_at is None:
        raise NotLeftYet(f"{seating_public_id}: the party has not left; clear comes after leave")
    if seating.cleared_at is not None:
        raise AlreadyCleared(f"{seating_public_id} was cleared at {seating.cleared_at:%H:%M}")
    now = clock.now()
    table = session.get(DiningTable, seating.table_id)
    # One transaction — the seating, the table and the party.
    seating.cleared_at = now
    seating.turn_minutes = minutes_between(seating.seated_at, seating.left_at)   # what the table earned, not what the server took
    table.current_seating_id = None
    table.cleared_at = now
    party = session.get(Party, seating.party_id)
    party.state = "cleared"
    session.commit()
    return seating, table