from fastapi import APIRouter

from ..schemas import SettingsOut
from ..services.seed import BRANCH
from ..services.tables import get_branch, max_covers
from . import SessionDep, SettingsDep

router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=SettingsOut, summary="The rules in force (read-only)")
def get_settings_(session: SessionDep, settings: SettingsDep) -> SettingsOut:
    branch = get_branch(session, BRANCH[0])
    return SettingsOut(default_quote_minutes=settings.default_quote_minutes, small_party_upgrade=settings.small_party_upgrade,
                       max_covers=max_covers(session, branch.id))


        