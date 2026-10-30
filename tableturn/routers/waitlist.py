from fastapi import APIRouter, Response

from ..errors import PartyTooBig
from ..handlers import VALIDATION_RESPONSE, responses
from ..ids import party_public
from ..schemas import JoinIn, JoinOut
from ..services import waitlist
from ..services.seed import BRANCH
from ..services.tables import get_branch
from . import ClockDep, SessionDep, SettingsDep

router = APIRouter(prefix="/waitlist", tags=["waitlist"])


@router.post(
    "", response_model=JoinOut, status_code=201, summary="A party joins the list and is quoted a wait",
    responses={201: {"description": "On the list", "headers": {"Location": {
                   "schema": {"type": "string"}, "description": "Where the party can be read: /parties/{party_id}"}}},
               **responses((PartyTooBig, "No table in Baner seats 9; the largest seats 6", {"max_covers": 6})),
               **VALIDATION_RESPONSE},
)
def join(body: JoinIn, response: Response, session: SessionDep, clock: ClockDep, settings: SettingsDep) -> JoinOut:
    branch = get_branch(session, BRANCH[0])
    party = waitlist.join(session, branch, body.name, body.covers, body.phone, clock, settings)
    out = JoinOut(party_id=party_public(party.id), name=party.name, covers=party.covers, position=party.position,
                  joined_at=party.joined_at, quoted_minutes=party.quoted_minutes, quoted_at=party.quoted_at)
    response.headers["Location"] = f"/parties/{out.party_id}"
    return out