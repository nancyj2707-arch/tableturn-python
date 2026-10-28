"""A party joins the list. Position is computed at insert."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..clock import Clock
from ..errors import PartyTooBig
from ..models import Branch, Party
from .tables import max_covers


def join(session: Session, branch: Branch, name: str, covers: int, phone: str | None, clock: Clock) -> Party:
    largest = max_covers(session, branch.id)
    if covers > largest:
        raise PartyTooBig(f"No table in {branch.code} seats {covers}; the largest seats {largest}", max_covers=largest)
    now = clock.now()
    waiting = session.scalar(select(func.count()).select_from(Party).where(Party.branch_id == branch.id, Party.state == "waiting"))
    party = Party(branch_id=branch.id, name=name, covers=covers, phone=phone, state="waiting", joined_at=now,
                  position=int(waiting) + 1)
    session.add(party)
    session.flush()
    session.commit()
    return party