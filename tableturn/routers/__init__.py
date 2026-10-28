"""Routes parse and delegate; they hold no rules. The request-scoped dependencies live
here, so nothing below the routers (services, rules, settings, db) imports FastAPI."""
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from ..clock import Clock, get_clock


def get_session(request: Request) -> Iterator[Session]:
    """One session per request. Closing it rolls back whatever the request did not commit, so a failure half-way
    through a service leaves nothing behind."""
    with request.app.state.sessionmaker() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
ClockDep = Annotated[Clock, Depends(get_clock)]