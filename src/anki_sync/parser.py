import re
from dataclasses import dataclass


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
