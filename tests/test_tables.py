"""22 tables loaded once, a floor filterable by section and state, state derived — never stored."""
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from tableturn.app import create_app
from tableturn.models import DiningTable
from tests.conftest import make_settings


def test_seeding_is_idempotent_across_two_starts(tmp_path, clock):
    settings = make_settings(tmp_path)
    for _ in range(2):
        app = create_app(settings)
        with TestClient(app) as c:
            assert c.get("/branches/Baner/tables").json()["free"] == 22
        with app.state.sessionmaker() as s:
            assert s.scalar(select(func.count()).select_from(DiningTable)) == 22
            

def test_floor_has_twenty_two_tables_all_free(client):
    r = client.get("/branches/Baner/tables")
    assert r.status_code == 200
    body = r.json()
    assert body["branch"] == "Baner" and body["free"] == 22 and len(body["tables"]) == 22
    seats = [t["seats"] for t in body["tables"]]
    assert seats.count(2) == 10 and seats.count(4) == 8 and seats.count(6) == 4
    assert all(t["state"] == "free" for t in body["tables"])
    # a free table carries exactly the contract's keys — no party, no seating, no null placeholders.
    assert all(set(t) == {"no", "seats", "section", "state"} for t in body["tables"])
    assert {t["section"] for t in body["tables"]} == {"Window", "Garden", "Indoor"}


def test_section_filter_returns_only_that_section_and_its_free_count(client):
    r = client.get("/branches/Baner/tables?section=Garden")
    body = r.json()
    assert body["tables"] and all(t["section"] == "Garden" for t in body["tables"])
    assert body["free"] == len(body["tables"]) == 8
    

def test_unknown_filter_values_are_400_not_an_empty_list(client):
    r = client.get("/branches/Baner/tables?section=Roof")
    assert r.status_code == 400
    body = r.json()
    assert body["type"] == "/errors/validation" and body["errors"][0]["field"] == "section"
    r = client.get("/branches/Baner/tables?state=busy")
    assert r.status_code == 400 and r.json()["errors"][0]["field"] == "state"


def test_one_table_and_the_404s(client):
    r = client.get("/branches/Baner/tables/T11")
    assert r.status_code == 200 and r.json() == {"no": "T11", "seats": 4, "section": "Garden", "state": "free"}
    r = client.get("/branches/Baner/tables/T99")
    assert r.status_code == 404 and r.json()["type"] == "/errors/no-such-table"
    r = client.get("/branches/Aundh/tables")
    assert r.status_code == 404 and r.json()["type"] == "/errors/no-such-branch"
    r = client.get("/branches/Aundh/tables/T11")
    assert r.status_code == 404 and r.json()["type"] == "/errors/no-such-branch"


def test_there_is_no_stored_state_column():
    assert "state" not in DiningTable.__table__.columns