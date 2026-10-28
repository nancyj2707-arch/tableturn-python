from fastapi import APIRouter, Response

from ..ids import party_public
from ..schemas import JoinIn, JoinOut
from ..services import waitlist
from ..services.seed import BRANCH
from ..services.tables import get_branch
from . import ClockDep, SessionDep

router = APIRouter(prefix="/waitlist")


@router.post(
    "", response_model=JoinOut, status_code=201,
)
def join(body: JoinIn, response: Response, session: SessionDep, clock: ClockDep) -> JoinOut:
    branch = get_branch(session, BRANCH[0])
    party = waitlist.join(session, branch, body.name, body.covers, body.phone, clock)
    out = JoinOut(party_id=party_public(party.id), name=party.name, covers=party.covers, position=party.position,
                  joined_at=party.joined_at)
    response.headers["Location"] = f"/parties/{out.party_id}"
    return out