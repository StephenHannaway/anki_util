import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from anki_sync.parser import Card


class AnkiConnectionError(Exception):
    pass


@dataclass
class SyncResult:
    added: int
    updated: int
    deleted: int
    total: int


class AnkiClient:
    def __init__(self, url: str = "http://localhost:8765") -> None:
        self._url = url

    def _request(self, action: str, **params: Any) -> Any:
        payload = json.dumps(
            {"action": action, "version": 6, "params": params}
        ).encode()
        try:
            with urllib.request.urlopen(self._url, data=payload, timeout=5) as resp:
                result: dict[str, Any] = json.loads(resp.read())
        except urllib.error.URLError as exc:
            raise AnkiConnectionError(
                "Anki is not open — start Anki and try again"
            ) from exc
        if result.get("error"):
            raise RuntimeError(f"AnkiConnect error: {result['error']}")
        if "result" not in result:
            raise RuntimeError(f"Malformed AnkiConnect response: {result!r}")
        return result["result"]

    def sync_deck(self, deck_name: str, cards: list[Card]) -> SyncResult:
        self._request("createDeck", deck=deck_name)

        note_ids: list[int] = self._request("findNotes", query=f'deck:"{deck_name}"')
        existing: dict[str, dict[str, Any]] = {}

        if note_ids:
            notes_info: list[dict[str, Any]] = self._request(
                "notesInfo", notes=note_ids
            )
            for note in notes_info:
                front: str = note["fields"]["Front"]["value"]
                existing[front] = {
                    "id": note["noteId"],
                    "back": note["fields"]["Back"]["value"],
                    "tags": note["tags"],
                }

        to_delete = {info["id"] for info in existing.values()}
        added = updated = 0

        for card in cards:
            if card.front in existing:
                to_delete.discard(existing[card.front]["id"])
            else:
                self._request(
                    "addNote",
                    note={
                        "deckName": deck_name,
                        "modelName": "Basic",
                        "fields": {"Front": card.front, "Back": card.back},
                        "tags": [card.tag] if card.tag else [],
                    },
                )
                added += 1

        deleted = len(to_delete)
        if to_delete:
            self._request("deleteNotes", notes=list(to_delete))

        return SyncResult(
            added=added, updated=updated, deleted=deleted, total=len(cards)
        )
