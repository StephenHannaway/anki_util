import os
from pathlib import Path
from unittest.mock import patch

import pytest

from anki_sync.main import flashcard_file, get_vault_path


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
        tmp_path
        / "09 \u00b7 Flashcards"
        / "AWS Compute"
        / "AWS Compute - Flashcards.md"
    )
    assert result == expected
