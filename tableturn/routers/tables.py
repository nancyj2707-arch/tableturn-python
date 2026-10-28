from fastapi import APIRouter

from ..schemas import FloorOut, Section, TableOut, TableState
from ..services import tables
from . import ClockDep, SessionDep

router = APIRouter(prefix="/branches/{branch}/tables")


@router.get(
    "", response_model=FloorOut, response_model_exclude_none=True,
)
def list_tables(branch: str, session: SessionDep, clock: ClockDep,
                section: Section | None = None, state: TableState | None = None) -> FloorOut:
    return tables.list_tables(session, branch, section, state, clock)


@router.get(
    "/{no}", response_model=TableOut, response_model_exclude_none=True,
)
def get_table(branch: str, no: str, session: SessionDep, clock: ClockDep) -> TableOut:
    return tables.get_table(session, branch, no, clock)