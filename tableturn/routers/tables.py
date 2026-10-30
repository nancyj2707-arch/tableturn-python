from fastapi import APIRouter

from ..errors import NoSuchBranch, NoSuchTable
from ..handlers import FILTER_RESPONSE, responses
from ..schemas import FloorOut, Section, TableOut, TableState
from ..services import tables
from . import ClockDep, SessionDep

router = APIRouter(prefix="/branches/{branch}/tables", tags=["tables"])

NO_BRANCH = (NoSuchBranch, "There is no branch 'Aundh'")


@router.get(
    "", response_model=FloorOut, response_model_exclude_none=True, summary="The floor: every table with its derived state",
    responses={**responses(NO_BRANCH), **FILTER_RESPONSE},
)
def list_tables(branch: str, session: SessionDep, clock: ClockDep,
                section: Section | None = None, state: TableState | None = None) -> FloorOut:
    return tables.list_tables(session, branch, section, state, clock)


@router.get(
    "/{no}", response_model=TableOut, response_model_exclude_none=True, summary="One table",
    responses=responses(NO_BRANCH, (NoSuchTable, "There is no table 'T99' in branch Baner")),
)
def get_table(branch: str, no: str, session: SessionDep, clock: ClockDep) -> TableOut:
    return tables.get_table(session, branch, no, clock)