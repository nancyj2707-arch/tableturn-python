"""Three refusals, each its own type and status, raised from the service and mapped once."""
import ast
from pathlib import Path

import pytest

from tableturn.handlers import PROBLEM
from tests.conftest import join, seat, seated

PKG = Path(__file__).resolve().parent.parent / "tableturn"


def test_table_too_small(client):
    party = join(client, 6)
    r = seat(client, party["party_id"], "T11")
    assert r.status_code == 409 and r.json()["type"] == "/errors/table-too-small"


def test_already_seated(client):
    s = seated(client, 6, "T20")
    r = seat(client, s["party_id"], "T21")
    assert r.status_code == 409 and r.json()["type"] == "/errors/already-seated"


def test_table_not_cleared_after_the_party_left(client):
    s = seated(client, 2, "T01")
    assert client.post(f"/seatings/{s['seating_id']}/leave").status_code == 200
    party = join(client, 2)
    r = seat(client, party["party_id"], "T01")
    assert r.status_code == 409 and r.json()["type"] == "/errors/table-not-cleared"


def test_an_occupied_table_is_refused_the_same_way(client):
    seated(client, 2, "T01")
    party = join(client, 2)
    r = seat(client, party["party_id"], "T01")
    assert r.status_code == 409 and r.json()["type"] == "/errors/table-not-cleared"


def test_the_404s_and_the_order_of_checks(client):
    """party exists → table exists → party not already seated → table cleared → table fits; the first failure wins."""
    party = join(client, 2)
    r = seat(client, party["party_id"], "T99")
    assert r.status_code == 404 and r.json()["type"] == "/errors/no-such-table"
    r = seat(client, "W999", "T99")
    assert r.status_code == 404 and r.json()["type"] == "/errors/no-such-party", "the party is checked before the table"
    s = seated(client, 6, "T20")
    r = seat(client, s["party_id"], "T99")             # already seated AND no such table: the table is checked first
    assert r.status_code == 404 and r.json()["type"] == "/errors/no-such-table"
    r = seat(client, s["party_id"], "T01")             # already seated AND too small: already-seated wins
    assert r.json()["type"] == "/errors/already-seated"
    four = seated(client, 4, "T12")
    assert client.post(f"/seatings/{four['seating_id']}/leave").status_code == 200
    six = join(client, 6)
    r = seat(client, six["party_id"], "T12")           # not cleared AND too small: not-cleared wins
    assert r.status_code == 409 and r.json()["type"] == "/errors/table-not-cleared"


def _too_small(client):
    return seat(client, join(client, 6)["party_id"], "T11"), set()


def _too_big(client):
    return client.post("/waitlist", json={"name": "Big", "covers": 9}), {"max_covers"}


def _overtaking(client):
    join(client, 4)
    return seat(client, join(client, 2)["party_id"], "T11"), {"must_seat_first"}
@pytest.mark.parametrize("make", [_too_small, _too_big, _overtaking], ids=["table-too-small", "party-too-big", "overtaking"])
def test_refusal_body_has_exactly_the_documented_shape(client, make):
    r, named = make(client)
    assert r.status_code in (400, 409)
    assert r.headers["content-type"].startswith(PROBLEM)
    assert set(r.json()) == {"type", "title", "status", "detail"} | named
    assert r.json()["status"] == r.status_code
    assert "Traceback" not in r.text and 'File "' not in r.text


def test_routes_never_build_error_responses():
    """No route raises, builds an `HTTPException` (bare or `fastapi.HTTPException`) or builds a `JSONResponse`."""
    for path in (PKG / "routers").glob("*.py"):
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        assert not any(isinstance(n, ast.Raise) for n in ast.walk(tree)), f"{path.name} raises inside a route"
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        imported = {a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
        for banned in ("HTTPException", "JSONResponse"):
            assert banned not in names and banned not in imported, f"{path.name} uses {banned}"