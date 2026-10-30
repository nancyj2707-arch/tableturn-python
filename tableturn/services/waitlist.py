"""A party joins the list. Position is computed at insert; the quote is stamped from the clock; the join
and the quote are written as events in the same transaction."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..clock import Clock
from ..errors import PartyTooBig
from ..models import Branch, Party
from ..settings import Settings
from . import events
from .tables import max_covers


def join(session: Session, branch: Branch, name: str, covers: int, phone: str | None, clock: Clock, settings: Settings) -> Party:
    largest = max_covers(session, branch.id)
    if covers > largest:
        raise PartyTooBig(f"No table in {branch.code} seats {covers}; the largest seats {largest}", max_covers=largest)
    now = clock.now()
    waiting = session.scalar(select(func.count()).select_from(Party).where(Party.branch_id == branch.id, Party.state == "waiting"))
    party = Party(branch_id=branch.id, name=name, covers=covers, phone=phone, state="waiting", joined_at=now,
                  position=int(waiting) + 1, quoted_minutes=settings.default_quote_minutes, quoted_at=now)
    session.add(party)
    session.flush()
    events.record(session, branch, party.id, "joined", now, {"covers": covers})
    events.record(session, branch, party.id, "quoted", now, {"quoted_minutes": party.quoted_minutes})
    session.commit()
    return party