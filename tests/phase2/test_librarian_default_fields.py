"""Guard test for the canonical librarian default-field list (#116).

Per Constitution Principle I the field list lives in exactly one place —
``llmxive.librarian.LIBRARIAN_DEFAULT_FIELDS`` — and both consumers
(`cli.py`'s per-field pipeline pass and the cross-domain coverage test)
import it. This test pins the expected contents (catching accidental
edits) and asserts the consumers really do use the canonical constant
rather than a stale copy.
"""

from __future__ import annotations

import re
from pathlib import Path

from llmxive.librarian import LIBRARIAN_DEFAULT_FIELDS

_EXPECTED = (
    "biology",
    "chemistry",
    "computer science",
    "materials science",
    "mathematics",
    "neuroscience",
    "physics",
    "psychology",
    "statistics",
)
_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_canonical_field_list_contents() -> None:
    assert LIBRARIAN_DEFAULT_FIELDS == _EXPECTED
    assert isinstance(LIBRARIAN_DEFAULT_FIELDS, tuple)  # immutable canonical


def test_cross_domain_test_uses_the_canonical_constant() -> None:
    # The cross-domain coverage test parametrizes over exactly the
    # canonical list (so it always covers what the CLI actually uses).
    from tests.phase2 import test_librarian_cross_domain as cd

    assert list(cd.DEFAULT_FIELDS) == list(LIBRARIAN_DEFAULT_FIELDS)


def test_no_third_copy_of_the_field_list() -> None:
    # Acceptance criterion from #116: the literal list ("biology" …
    # "computer science" …) appears defined exactly once in the repo —
    # in src/llmxive/librarian/__init__.py. (Test fixtures / this test
    # itself may list the fields; we scan only src/ + the CLI/lib code.)
    pat = re.compile(r'"biology"[\s,]+"chemistry"[\s,]+"computer science"', re.S)
    hits = []
    for path in (_REPO_ROOT / "src" / "llmxive").rglob("*.py"):
        if pat.search(path.read_text(encoding="utf-8")):
            hits.append(path.relative_to(_REPO_ROOT).as_posix())
    assert hits == ["src/llmxive/librarian/__init__.py"], hits
