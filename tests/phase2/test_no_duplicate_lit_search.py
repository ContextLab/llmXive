"""FR-022 enforcement guardrail (spec 005 / T070a).

Catches re-introduction of duplicate literature-search implementations
outside the canonical librarian package. Constitution Principle I
forbids parallel implementations of the same capability — the librarian
is the single source of truth for search + verify.

This test fails if any file under ``src/llmxive/`` or ``agents/`` (other
than the librarian package itself + the soft-deprecated shims) contains
BOTH the Semantic Scholar API host AND the arXiv API endpoint. A file
with both is highly likely to be a parallel lit-search implementation
masquerading as something else.

Allow-listed files (these are the canonical or intentionally-deprecated
locations and are exempt):

  - src/llmxive/librarian/**           (the canonical implementation)
  - agents/tools/lit_search.py         (soft-deprecated shim, FR-014/15)
  - agents/tools/citation_fetcher.py   (soft-deprecated shim, FR-014/15)
  - tests/phase1/citation_resolver.py  (soft-deprecated shim, FR-014/15)
  - tests/                             (test fixtures may legitimately
                                        reference both endpoints)
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Substrings indicating a Semantic Scholar OR arXiv API caller.
SS_MARKERS = ("api.semanticscholar.org", "semanticscholar.org/graph")
ARXIV_MARKERS = ("export.arxiv.org/api/query", "arxiv.org/api/query")

ALLOWED_PATH_PREFIXES = (
    "src/llmxive/librarian/",
    "agents/tools/lit_search.py",
    "agents/tools/citation_fetcher.py",
    "tests/phase1/citation_resolver.py",
)

SCAN_ROOTS = (
    REPO_ROOT / "src" / "llmxive",
    REPO_ROOT / "agents",
)


def _is_allowed(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT).as_posix()
    return any(rel.startswith(p) or rel == p for p in ALLOWED_PATH_PREFIXES)


def _file_has_both_markers(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    has_ss = any(m in text for m in SS_MARKERS)
    has_arxiv = any(m in text for m in ARXIV_MARKERS)
    return has_ss and has_arxiv


def test_no_duplicate_lit_search_implementation():
    """Fail loudly if a non-allow-listed file carries both backend
    references — that's almost certainly a parallel implementation."""
    offenders: list[str] = []
    for root in SCAN_ROOTS:
        if not root.is_dir():
            continue
        for py in root.rglob("*.py"):
            if _is_allowed(py):
                continue
            if _file_has_both_markers(py):
                offenders.append(py.relative_to(REPO_ROOT).as_posix())

    assert not offenders, (
        "FR-022 violation (Constitution Principle I): the following file(s) "
        "appear to contain a parallel lit-search implementation referencing "
        "both Semantic Scholar AND arXiv APIs. Use "
        "`from llmxive.librarian.search import SemanticScholarClient, "
        "ArxivClient` instead. Offenders:\n  - "
        + "\n  - ".join(offenders)
    )
