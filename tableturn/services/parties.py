"""One party — what they were quoted, what they waited, where they sat, and every transition."""
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..clock import as_utc
from ..errors import NoSuchParty
from ..ids import party_internal, party_public
from ..models import Branch, DiningTable, Event, Party, Seating
from ..schemas import EventOut, PartyOut


def get_party(session: Session, branch: Branch, public_id: str) -> PartyOut:
    internal = party_internal(public_id)
    party = session.get(Party, internal) if internal is not None else None
    if party is None or party.branch_id != branch.id:
        raise NoSuchParty(f"There is no party {public_id!r} on the {branch.code} list")
    seating = session.scalar(select(Seating).where(Seating.party_id == party.id).order_by(Seating.id.desc()).limit(1))
    table_no = session.get(DiningTable, seating.table_id).no if seating is not None else None
    rows = session.scalars(select(Event).where(Event.party_id == party.id).order_by(Event.at, Event.id)).all()
    return PartyOut(
        party_id=party_public(party.id), name=party.name, covers=party.covers, state=party.state, position=party.position,
        joined_at=as_utc(party.joined_at), quoted_minutes=party.quoted_minutes, quoted_at=as_utc(party.quoted_at),
        waited_minutes=party.waited_minutes, table=table_no,
        events=[EventOut(at=as_utc(e.at), kind=e.kind, **json.loads(e.data)) for e in rows],
    )