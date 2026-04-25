import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from anki_sync.anki import SyncResult
from anki_sync.main import flashcard_file, get_vault_path, sync_topic


def test_get_vault_path_returns_path_from_env(tmp_path: Path) -> None:
    with patch.dict(os.environ, {"SECOND_BRAIN_PATH": str(tmp_path)}):
        assert get_vault_path() == tmp_path


def test_get_vault_path_exits_when_env_not_set() -> None:
    env = {k: v for k, v in os.environ.items() if k != "SECOND_BRAIN_PATH"}
    with patch.dict(os.environ, env, clear=True), pytest.raises(SystemExit):
        get_vault_path()


def test_flashcard_file_constructs_correct_path(tmp_path: Path) -> None:
    result = flashcard_file(tmp_path, "AWS Compute")
    expected = (
        tmp_path / "FLASHCARDS_DIR" / "AWS Compute" / "AWS Compute - Flashcards.md"
    )
    assert result == expected


def test_sync_topic_prints_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Create a real flashcard file in the expected location
    deck_dir = tmp_path / "FLASHCARDS_DIR" / "AWS Compute"
    deck_dir.mkdir(parents=True)
    (deck_dir / "AWS Compute - Flashcards.md").write_text(
        "What is EC2? :: Elastic Compute Cloud\n", encoding="utf-8"
    )

    client = MagicMock()
    client.sync_deck.return_value = SyncResult(added=1, updated=0, deleted=0, total=1)

    sync_topic(client, tmp_path, "AWS Compute")

    captured = capsys.readouterr()
    assert captured.out == "AWS Compute: 1 added, 0 updated, 0 deleted (1 total)\n"


def test_sync_topic_exits_when_file_missing(tmp_path: Path) -> None:
    client = MagicMock()
    with pytest.raises(SystemExit):
        sync_topic(client, tmp_path, "AWS Compute")
