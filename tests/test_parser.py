from anki_sync.parser import Card, _normalise_tag


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
