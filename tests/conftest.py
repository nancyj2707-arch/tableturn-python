"""Every test gets its own SQLite file, a fixed clock it can move, and the seed files from the repo."""
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tableturn.app import create_app
from tableturn.clock import FixedClock, get_clock
from tableturn.settings import Settings

ROOT = Path(__file__).resolve().parent.parent
T0 = datetime(2026, 9, 27, 19, 10, tzinfo=timezone.utc)      # Sunday, ten past seven: the Kulkarnis arrive


def make_settings(tmp_path: Path, **overrides) -> Settings:
    db = (tmp_path / "tableturn-test.db").as_posix()
    values = {"database_url": f"sqlite:///{db}", "seed_dir": str(ROOT / "seed"), "free_window_hours": 48, "default_quote_minutes": 40,
              "small_party_upgrade": "when_nobody_larger_waits"}
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(T0)


@pytest.fixture
def settings(tmp_path) -> Settings:
    return make_settings(tmp_path)


@pytest.fixture
def app(settings, clock):
    app = create_app(settings)
    app.dependency_overrides[get_clock] = lambda: clock
    return app


@pytest.fixture
def client(app):
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def db(app):
    """A fresh session factory for looking at rows the API wrote."""
    return app.state.sessionmaker


def join(client, covers=6, name="Kulkarni", phone=None) -> dict:
    body = {"name": name, "covers": covers}
    if phone:
        body["phone"] = phone
    r = client.post("/waitlist", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def seat(client, party_id, table):
    return client.post("/seatings", json={"party_id": party_id, "table": table})


def seated(client, covers=6, table="T20") -> dict:
    """join + seat, returning the seating body."""
    party = join(client, covers)
    r = seat(client, party["party_id"], table)
    assert r.status_code == 201, r.text
    return r.json()