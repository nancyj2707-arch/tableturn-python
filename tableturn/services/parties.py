"""One party — what they were quoted, what they waited and where they sat."""
from sqlalchemy.orm import Session

from ..clock import as_utc
from ..errors import NoSuchParty
from ..ids import party_internal, party_public
from ..models import Branch, Party
from ..schemas import PartyOut


def get_party(session: Session, branch: Branch, public_id: str) -> PartyOut:
    internal = party_internal(public_id)
    party = session.get(Party, internal) if internal is not None else None
    if party is None or party.branch_id != branch.id:
        raise NoSuchParty(f"There is no party {public_id!r} on the {branch.code} list")
    return PartyOut(
        party_id=party_public(party.id), name=party.name, covers=party.covers, state=party.state, position=party.position,
        joined_at=as_utc(party.joined_at), quoted_minutes=party.quoted_minutes, quoted_at=as_utc(party.quoted_at),
        waited_minutes=party.waited_minutes,
    )