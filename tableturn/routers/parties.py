from fastapi import APIRouter

from ..schemas import PartyOut
from ..services import parties
from ..services.seed import BRANCH
from ..services.tables import get_branch
from . import SessionDep

router = APIRouter(prefix="/parties")


@router.get(
    "/{party_id}", response_model=PartyOut, response_model_exclude_none=True,
)
def get_party(party_id: str, session: SessionDep) -> PartyOut:
    return parties.get_party(session, get_branch(session, BRANCH[0]), party_id)