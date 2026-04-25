import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from anki_sync.anki import AnkiClient, AnkiConnectionError
from anki_sync.parser import parse_flashcard_file

load_dotenv()

FLASHCARDS_DIR = "09 \u00b7 Flashcards"


def get_vault_path() -> Path:
    raw = os.environ.get("SECOND_BRAIN_PATH", "")
    if not raw:
        print(
            "Error: SECOND_BRAIN_PATH not set. Add it to your .env file.",
            file=sys.stderr,
        )
        sys.exit(1)
    return Path(raw)


def get_anki_url() -> str:
    return os.environ.get("ANKI_CONNECT_URL", "http://localhost:8765")


def flashcard_file(vault: Path, topic: str) -> Path:
    return vault / FLASHCARDS_DIR / topic / f"{topic} - Flashcards.md"


def sync_topic(client: AnkiClient, vault: Path, topic: str) -> None:
    path = flashcard_file(vault, topic)
    if not path.exists():
        print(f"No flashcard file found for '{topic}'", file=sys.stderr)
        sys.exit(1)
    cards = parse_flashcard_file(path)
    result = client.sync_deck(topic, cards)
    print(
        f"{topic}: {result.added} added, {result.updated} updated, "
        f"{result.deleted} deleted ({result.total} total)"
    )


def sync_all(client: AnkiClient, vault: Path) -> None:
    flashcards_root = vault / FLASHCARDS_DIR
    topics = sorted(d.name for d in flashcards_root.iterdir() if d.is_dir())
    if not topics:
        print("No flashcard decks found.", file=sys.stderr)
        sys.exit(1)
    for topic in topics:
        path = flashcard_file(vault, topic)
        if not path.exists():
            print(f"No flashcard file found for '{topic}', skipping.", file=sys.stderr)
            continue
        sync_topic(client, vault, topic)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Obsidian flashcards to Anki")
    parser.add_argument(
        "topic", nargs="?", help='Deck name to sync (e.g. "AWS Compute")'
    )
    parser.add_argument("--all", action="store_true", help="Sync all decks")
    args = parser.parse_args()

    if not args.all and not args.topic:
        parser.error("Specify a topic or use --all")
    if args.all and args.topic:
        parser.error("Cannot specify both a topic and --all")

    vault = get_vault_path()
    client = AnkiClient(url=get_anki_url())

    try:
        if args.all:
            sync_all(client, vault)
        else:
            if args.topic:
                sync_topic(client, vault, args.topic)
    except AnkiConnectionError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
