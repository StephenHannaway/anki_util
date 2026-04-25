import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Card:
    front: str
    back: str
    tag: str


def _normalise_tag(heading: str) -> str:
    text = heading.lstrip("#").strip()
    text = re.sub(r"[\s\u2013\u2014\u2015]+", "-", text)
    text = re.sub(r"[^\w-]", "", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def parse_flashcard_file(path: Path) -> list[Card]:
    lines = path.read_text(encoding="utf-8").splitlines()
    cards: list[Card] = []
    current_tag = ""
    in_frontmatter = False

    for i, line in enumerate(lines):
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if line.strip() == "---":
                in_frontmatter = False
            continue
        if line.strip().startswith("<!--SR:"):
            continue
        if line.startswith("## "):
            current_tag = _normalise_tag(line)
            continue
        if " :: " in line:
            front, _, back = line.partition(" :: ")
            cards.append(Card(front=front.strip(), back=back.strip(), tag=current_tag))

    return cards
