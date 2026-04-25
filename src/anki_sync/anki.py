import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


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
        except (urllib.error.URLError, OSError) as exc:
            raise AnkiConnectionError(
                "Anki is not open — start Anki and try again"
            ) from exc
        if result.get("error"):
            raise RuntimeError(f"AnkiConnect error: {result['error']}")
        return result["result"]
