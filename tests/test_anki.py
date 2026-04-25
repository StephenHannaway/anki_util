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
            None,  # addNote
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
