from fastapi import APIRouter

from ..ids import party_public, seating_public
from ..models import Party
from ..schemas import SeatIn, SeatOut
from ..services import seatings
from ..services.seed import BRANCH
from ..services.tables import get_branch
from . import ClockDep, SessionDep

router = APIRouter(prefix="/seatings")


@router.post(
    "", response_model=SeatOut, status_code=201,
)
def seat(body: SeatIn, session: SessionDep, clock: ClockDep) -> SeatOut:
    branch = get_branch(session, BRANCH[0])
    seating = seatings.seat(session, branch, body.party_id, body.table, clock)
    return SeatOut(seating_id=seating_public(seating.id), party_id=party_public(seating.party_id), table=body.table,
                   seated_at=seating.seated_at, waited_minutes=session.get(Party, seating.party_id).waited_minutes)