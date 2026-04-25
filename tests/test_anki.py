import json
import urllib.error
from unittest.mock import patch

import pytest

from anki_sync.anki import AnkiClient, AnkiConnectionError


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
