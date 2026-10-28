"""A party joins the list; an impossible size and a malformed body are refused differently."""
from sqlalchemy import func, select

from tableturn.models import Party
from tests.conftest import join


def test_a_party_joins_and_gets_an_id_a_position_and_a_location(client, db):
    r = client.post("/waitlist", json={"name": "Kulkarni", "covers": 6, "phone": "+919876543210"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["party_id"] == "W001" and body["position"] == 1 and body["covers"] == 6 and body["name"] == "Kulkarni"
    assert body["joined_at"] == "2026-09-27T19:10:00Z"
    assert r.headers["location"] == "/parties/W001"
    with db() as s:
        row = s.get(Party, 1)
        assert row.state == "waiting" and row.phone == "+919876543210"


def test_position_is_one_plus_the_parties_waiting(client):
    assert join(client, 2)["position"] == 1
    assert join(client, 4)["position"] == 2
    assert join(client, 6)["position"] == 3


def test_nine_covers_is_party_too_big_and_writes_no_row(client, db):
    r = client.post("/waitlist", json={"name": "Big", "covers": 9})
    assert r.status_code == 400
    body = r.json()
    assert body["type"] == "/errors/party-too-big" and body["max_covers"] == 6
    with db() as s:
        assert s.scalar(select(func.count()).select_from(Party)) == 0


def test_malformed_bodies_are_422_naming_the_field(client):
    for body, field in (({"name": "", "covers": 2}, "name"), ({"name": "Rao", "covers": 0}, "covers"),
                        ({"name": "Rao", "covers": 21}, "covers"), ({"name": "Rao", "covers": 2, "phone": "98765"}, "phone"),
                        ({"covers": 2}, "name")):
        r = client.post("/waitlist", json=body)
        assert r.status_code == 422, body
        assert r.json()["type"] == "/errors/validation" and field in {e["field"] for e in r.json()["errors"]}, body


def test_read_one_party_and_the_404(client):
    party = join(client, 6)
    r = client.get(f"/parties/{party['party_id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "waiting" and body["position"] == 1 and body["covers"] == 6
    assert "table" not in body and "waited_minutes" not in body, "a waiting party has no table and no real wait yet"
    r = client.get("/parties/W999")
    assert r.status_code == 404 and r.json()["type"] == "/errors/no-such-party"