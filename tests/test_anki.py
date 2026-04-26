import json
import urllib.error
from unittest.mock import patch

import pytest

from anki_sync.anki import AnkiClient, AnkiConnectionError, SyncResult
from anki_sync.parser import Card


@pytest.fixture
def client() -> AnkiClient:
    return AnkiClient(url="http://localhost:8765")


def test_connection_error_raises_anki_connection_error(client: AnkiClient) -> None:
    with (
        patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")),
        pytest.raises(AnkiConnectionError, match="Anki is not open"),
    ):
        client._request("deckNames")


def test_ankiconnect_error_in_response_raises_runtime_error(client: AnkiClient) -> None:
    body = json.dumps({"result": None, "error": "deck not found"}).encode()

    class FakeResponse:
        def read(self) -> bytes:
            return body

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            pass

    with (
        patch("urllib.request.urlopen", return_value=FakeResponse()),
        pytest.raises(RuntimeError, match="AnkiConnect error"),
    ):
        client._request("deckNames")


def test_successful_request_returns_result(client: AnkiClient) -> None:
    body = json.dumps({"result": ["DeckA", "DeckB"], "error": None}).encode()

    class FakeResponse:
        def read(self) -> bytes:
            return body

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            pass

    with patch("urllib.request.urlopen", return_value=FakeResponse()):
        result = client._request("deckNames")

    assert result == ["DeckA", "DeckB"]


def test_adds_new_cards_to_empty_deck(client: AnkiClient) -> None:
    cards = [Card(front="Q1", back="A1", tag="Tag1")]

    with patch.object(
        client,
        "_request",
        side_effect=[
            1,  # createDeck → deck id
            [],  # findNotes → empty deck
            100,  # addNote → note id
        ],
    ):
        result = client.sync_deck("Test Deck", cards)

    assert result == SyncResult(added=1, updated=0, deleted=0, total=1)


def test_empty_cards_on_empty_deck(client: AnkiClient) -> None:
    with patch.object(
        client,
        "_request",
        side_effect=[
            1,  # createDeck
            [],  # findNotes
        ],
    ):
        result = client.sync_deck("Test Deck", [])

    assert result == SyncResult(added=0, updated=0, deleted=0, total=0)


def _make_notes_info(notes):  # type: ignore[no-untyped-def]
    return [
        {
            "noteId": n["id"],
            "fields": {
                "Front": {"value": n["front"]},
                "Back": {"value": n["back"]},
            },
            "tags": n.get("tags", []),
        }
        for n in notes
    ]


def test_deletes_cards_absent_from_md(client: AnkiClient) -> None:
    cards = [Card(front="Q1", back="A1", tag="Tag1")]
    notes_info = _make_notes_info(
        [
            {"id": 100, "front": "Q1", "back": "A1", "tags": ["Tag1"]},
            {"id": 101, "front": "Q2", "back": "A2", "tags": ["Tag1"]},  # not in cards
        ]
    )

    with patch.object(
        client,
        "_request",
        side_effect=[
            1,  # createDeck
            [100, 101],  # findNotes
            notes_info,  # notesInfo
            None,  # deleteNotes
        ],
    ):
        result = client.sync_deck("Test Deck", cards)

    assert result == SyncResult(added=0, updated=0, deleted=1, total=1)


def test_no_update_when_card_unchanged(client: AnkiClient) -> None:
    cards = [Card(front="Q1", back="A1", tag="Tag1")]
    notes_info = _make_notes_info(
        [{"id": 100, "front": "Q1", "back": "A1", "tags": ["Tag1"]}]
    )

    with patch.object(
        client,
        "_request",
        side_effect=[
            1,  # createDeck
            [100],  # findNotes
            notes_info,  # notesInfo
        ],
    ):
        result = client.sync_deck("Test Deck", cards)

    assert result == SyncResult(added=0, updated=0, deleted=0, total=1)


def test_updates_back_when_changed(client: AnkiClient) -> None:
    cards = [Card(front="Q1", back="New answer", tag="Tag1")]
    notes_info = _make_notes_info(
        [{"id": 100, "front": "Q1", "back": "Old answer", "tags": ["Tag1"]}]
    )

    with patch.object(
        client,
        "_request",
        side_effect=[
            1,  # createDeck
            [100],  # findNotes
            notes_info,  # notesInfo
            None,  # updateNoteFields
        ],
    ):
        result = client.sync_deck("Test Deck", cards)

    assert result == SyncResult(added=0, updated=1, deleted=0, total=1)


def test_updates_tag_when_changed(client: AnkiClient) -> None:
    cards = [Card(front="Q1", back="A1", tag="NewTag")]
    notes_info = _make_notes_info(
        [{"id": 100, "front": "Q1", "back": "A1", "tags": ["OldTag"]}]
    )

    with patch.object(
        client,
        "_request",
        side_effect=[
            1,  # createDeck
            [100],  # findNotes
            notes_info,  # notesInfo
            None,  # addTags (NewTag not in existing tags)
        ],
    ):
        result = client.sync_deck("Test Deck", cards)

    assert result == SyncResult(added=0, updated=1, deleted=0, total=1)


def test_updates_back_and_tag_when_both_changed(client: AnkiClient) -> None:
    cards = [Card(front="Q1", back="New answer", tag="NewTag")]
    notes_info = _make_notes_info(
        [{"id": 100, "front": "Q1", "back": "Old answer", "tags": ["OldTag"]}]
    )

    with patch.object(
        client,
        "_request",
        side_effect=[
            1,  # createDeck
            [100],  # findNotes
            notes_info,  # notesInfo
            None,  # updateNoteFields
            None,  # addTags
        ],
    ):
        result = client.sync_deck("Test Deck", cards)

    assert result == SyncResult(added=0, updated=1, deleted=0, total=1)


def test_no_update_when_card_has_no_section_tag(client: AnkiClient) -> None:
    cards = [Card(front="Q1", back="A1", tag="")]  # no section tag
    notes_info = _make_notes_info(
        [{"id": 100, "front": "Q1", "back": "A1", "tags": ["OldTag"]}]
    )

    with patch.object(
        client,
        "_request",
        side_effect=[
            1,  # createDeck
            [100],  # findNotes
            notes_info,  # notesInfo
            # no update — untagged cards don't trigger tag updates
        ],
    ):
        result = client.sync_deck("Test Deck", cards)

    assert result == SyncResult(added=0, updated=0, deleted=0, total=1)


def test_duplicate_error_on_add_is_silently_skipped(client: AnkiClient) -> None:
    cards = [Card(front="Q1", back="A1", tag="Tag1")]

    def side_effect(action: str, **kwargs: object) -> object:
        if action == "createDeck":
            return 1
        if action == "findNotes":
            return []
        if action == "addNote":
            raise RuntimeError(
                "AnkiConnect error: cannot create note because it is a duplicate"
            )
        return None

    with patch.object(client, "_request", side_effect=side_effect):
        result = client.sync_deck("Test Deck", cards)

    assert result == SyncResult(added=0, updated=0, deleted=0, total=1)
