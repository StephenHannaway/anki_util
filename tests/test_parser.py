import textwrap
from pathlib import Path

from anki_sync.parser import Card, _normalise_tag, parse_flashcard_file


def test_normalise_plain_heading() -> None:
    assert _normalise_tag("## Lambda") == "Lambda"


def test_normalise_multi_word_heading() -> None:
    assert _normalise_tag("## ELB Types") == "ELB-Types"


def test_normalise_heading_with_em_dash() -> None:
    assert _normalise_tag("## EC2 — Core Concepts") == "EC2-Core-Concepts"


def test_normalise_heading_with_en_dash() -> None:
    assert _normalise_tag("## Auto Scaling \u2013 Policies") == "Auto-Scaling-Policies"


def test_normalise_heading_with_horizontal_bar() -> None:
    assert _normalise_tag("## S3 \u2015 Storage") == "S3-Storage"


def test_card_is_hashable() -> None:
    s = {Card(front="Q", back="A", tag="T")}
    assert Card(front="Q", back="A", tag="T") in s


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "cards.md"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def test_parse_basic_card(tmp_path: Path) -> None:
    path = _write(tmp_path, "What is EC2? :: Elastic Compute Cloud\n")
    assert parse_flashcard_file(path) == [
        Card(front="What is EC2?", back="Elastic Compute Cloud", tag="")
    ]


def test_skips_yaml_frontmatter(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """\
        ---
        title: Test
        tags:
          - flashcards/test
        ---
        What is EC2? :: Elastic Compute Cloud
        """,
    )
    cards = parse_flashcard_file(path)
    assert len(cards) == 1
    assert cards[0].front == "What is EC2?"


def test_skips_sr_scheduling_comments(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """\
        What is EC2? :: Elastic Compute Cloud
        <!--SR:!2026-04-25,1,230-->
        """,
    )
    assert len(parse_flashcard_file(path)) == 1


def test_section_heading_becomes_tag(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """\
        ## EC2 \u2014 Core Concepts
        What is EC2? :: Elastic Compute Cloud
        """,
    )
    assert parse_flashcard_file(path)[0].tag == "EC2-Core-Concepts"


def test_tag_follows_nearest_heading(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """\
        ## Section One
        Front one :: Back one
        ## Section Two
        Front two :: Back two
        """,
    )
    cards = parse_flashcard_file(path)
    assert cards[0].tag == "Section-One"
    assert cards[1].tag == "Section-Two"


def test_multiple_cards_same_section(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """\
        ## Lambda
        What is Lambda? :: Serverless compute
        How is Lambda priced? :: Invocations and duration
        """,
    )
    cards = parse_flashcard_file(path)
    assert len(cards) == 2
    assert all(c.tag == "Lambda" for c in cards)


def test_empty_file_returns_empty_list(tmp_path: Path) -> None:
    path = _write(tmp_path, "")
    assert parse_flashcard_file(path) == []
