"""The floor. A table's state is derived on read from its current seating — `seated` while the party is at
it, `uncleared` once they have left and nobody has wiped it, `free` otherwise. There is no stored state flag."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..clock import Clock, minutes_between
from ..errors import NoSuchBranch, NoSuchTable
from ..ids import party_public, seating_public
from ..models import Branch, DiningTable, Seating
from ..schemas import FloorOut, Section, TableOut, TableState


def get_branch(session: Session, code: str) -> Branch:
    branch = session.scalar(select(Branch).where(Branch.code == code))
    if branch is None:
        raise NoSuchBranch(f"There is no branch {code!r}")
    return branch


def max_covers(session: Session, branch_id: int) -> int:
    """The largest table in the branch — the biggest party that could ever be seated."""
    return int(session.scalar(select(func.max(DiningTable.seats)).where(DiningTable.branch_id == branch_id)) or 0)


def describe(session: Session, table: DiningTable, clock: Clock) -> TableOut:
    if table.current_seating_id is None:
        return TableOut(no=table.no, seats=table.seats, section=table.section, state="free")
    # seated while the current seating has no left_at; uncleared once it has (the clear empties current_seating_id and
    # writes tables.cleared_at, which nothing reads back).
    seating = session.get(Seating, table.current_seating_id)
    party_id, seating_id = party_public(seating.party_id), seating_public(seating.id)
    if seating.left_at is None:
        return TableOut(no=table.no, seats=table.seats, section=table.section, state="seated", party_id=party_id,
                        seating_id=seating_id, seated_minutes=minutes_between(seating.seated_at, clock.now()))
    return TableOut(no=table.no, seats=table.seats, section=table.section, state="uncleared", party_id=party_id,
                    seating_id=seating_id)


def list_tables(session: Session, branch_code: str, section: Section | None, state: TableState | None,
                clock: Clock) -> FloorOut:
    """The filters arrive already checked against their enums (the router types them), so `free` counts the free
    tables among those listed."""
    branch = get_branch(session, branch_code)
    rows = session.scalars(select(DiningTable).where(DiningTable.branch_id == branch.id).order_by(DiningTable.no)).all()
    described = [describe(session, t, clock) for t in rows]
    if section is not None:
        described = [t for t in described if t.section == section]
    if state is not None:
        described = [t for t in described if t.state == state]
    return FloorOut(branch=branch.code, free=sum(1 for t in described if t.state == "free"), tables=described)


def get_table(session: Session, branch_code: str, no: str, clock: Clock) -> TableOut:
    branch = get_branch(session, branch_code)
    table = session.scalar(select(DiningTable).where(DiningTable.branch_id == branch.id, DiningTable.no == no))
    if table is None:
        raise NoSuchTable(f"There is no table {no!r} in branch {branch.code}")
    return describe(session, table, clock)