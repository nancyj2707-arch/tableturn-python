from fastapi import APIRouter

from ..errors import NoSuchParty
from ..handlers import responses
from ..schemas import PartyOut
from ..services import parties
from ..services.seed import BRANCH
from ..services.tables import get_branch
from . import SessionDep

router = APIRouter(prefix="/parties", tags=["parties"])


@router.get(
    "/{party_id}", response_model=PartyOut, response_model_exclude_none=True,
    summary="One party: quote, real wait, table and every transition",
    responses=responses((NoSuchParty, "There is no party 'W999' on the Baner list")),
)
def get_party(party_id: str, session: SessionDep) -> PartyOut:
    return parties.get_party(session, get_branch(session, BRANCH[0]), party_id)