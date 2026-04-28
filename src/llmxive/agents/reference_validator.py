"""Reference-Validator Agent (T107).

Verifies citations against primary sources via
`agents/tools/citation_fetcher.py`. Writes to
`state/citations/<PROJ-ID>.yaml`.

The agent's runtime is intentionally NOT LLM-driven for the
verification decision (Constitution Principle II — verified means
verified by primary source, not by an LLM's opinion). The LLM is
optionally consulted for Mode A (citation extraction from artifact
text) and Mode B (human-readable summary), but the
`verification_status` field is computed deterministically.

Stage transitions: none. The Advancement-Evaluator reads the resulting
citations file and gates `research_accepted` / `paper_accepted` per
FR-028.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from llmxive.state import citations as citations_store
from llmxive.types import (
    Citation,
    CitationKind,
    Project,
    VerificationStatus,
)

LOGGER = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Citation extraction (regex-driven; no LLM required for the deterministic
# part). The extraction is conservative: it surfaces obvious patterns
# (URLs, arXiv ids, DOIs) and leaves nuance to the LLM in Mode A — but
# the rest of US7 only needs the deterministic extractor for v1.
# -----------------------------------------------------------------------------

_URL_RE = re.compile(r"https?://[^\s<>()\[\]\"']+", re.IGNORECASE)
_ARXIV_RE = re.compile(r"\barXiv:\s*(\d{4}\.\d{4,5})(v\d+)?\b", re.IGNORECASE)
_DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
_MARKDOWN_LINK_RE = re.compile(r"\[(?P<title>[^\]]+)\]\((?P<url>https?://[^\s)]+)\)")


@dataclass
class ExtractedCitation:
    cite_id: str
    kind: CitationKind
    value: str
    cited_title: str = ""


def extract_citations(artifact_text: str) -> list[ExtractedCitation]:
    """Conservatively pull URL / arXiv / DOI references from artifact text.

    Markdown link titles seed `cited_title` when present; otherwise the
    cited title is left empty (the validator then accepts any reachable
    URL as `verified` because there's no claim to mismatch against).
    """
    seen: set[tuple[str, str]] = set()
    out: list[ExtractedCitation] = []

    # Markdown links first — they carry titles.
    for i, m in enumerate(_MARKDOWN_LINK_RE.finditer(artifact_text)):
        url = m.group("url")
        key = ("url", url)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            ExtractedCitation(
                cite_id=f"c-{len(out) + 1:03d}",
                kind=CitationKind.URL,
                value=url,
                cited_title=m.group("title").strip(),
            )
        )

    # Bare URLs.
    for m in _URL_RE.finditer(artifact_text):
        url = m.group(0).rstrip(".,;:")
        key = ("url", url)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            ExtractedCitation(
                cite_id=f"c-{len(out) + 1:03d}",
                kind=CitationKind.URL,
                value=url,
            )
        )

    # arXiv ids.
    for m in _ARXIV_RE.finditer(artifact_text):
        ax = m.group(1)
        key = ("arxiv", ax)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            ExtractedCitation(
                cite_id=f"c-{len(out) + 1:03d}",
                kind=CitationKind.ARXIV,
                value=ax,
            )
        )

    # DOIs.
    for m in _DOI_RE.finditer(artifact_text):
        doi = m.group(0)
        key = ("doi", doi)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            ExtractedCitation(
                cite_id=f"c-{len(out) + 1:03d}",
                kind=CitationKind.DOI,
                value=doi,
            )
        )

    return out


# -----------------------------------------------------------------------------
# Validator — orchestrates extraction + fetch + persistence.
# -----------------------------------------------------------------------------


def validate_artifact(
    *,
    project_id: str,
    artifact_path: str,
    artifact_text: str,
    artifact_hash: str,
    repo_root: Path | None = None,
) -> list[Citation]:
    """Validate every external reference in `artifact_text`.

    Returns the persisted Citation records. Idempotent: re-validating
    the same artifact_hash overwrites only this artifact's entries —
    other projects' citations are untouched.
    """
    # Lazy import — citation_fetcher pulls httpx and (optionally) arxiv.
    import sys

    repo = repo_root or Path(__file__).resolve().parent.parent.parent.parent
    if str(repo) not in sys.path:  # pragma: no cover — defensive
        sys.path.insert(0, str(repo))
    from agents.tools.citation_fetcher import fetch_citation

    extracted = extract_citations(artifact_text)
    now = datetime.now(timezone.utc)

    # Read existing citations and drop any old entries for this artifact.
    existing = citations_store.load(project_id, repo_root=repo)
    kept: list[Citation] = [c for c in existing if c.artifact_path != artifact_path]

    new_records: list[Citation] = []
    for ext in extracted:
        result = fetch_citation(
            kind=ext.kind.value,
            value=ext.value,
            cited_title=ext.cited_title,
        )
        record = Citation(
            cite_id=ext.cite_id,
            artifact_path=artifact_path,
            artifact_hash=artifact_hash,
            kind=ext.kind,
            value=ext.value,
            cited_title=ext.cited_title or None,
            cited_authors=[],
            verification_status=result.status,
            verified_against_url=result.fetched_url or None,
            fetched_title=result.fetched_title or None,
            verified_at=now,
        )
        new_records.append(record)

    citations_store.save(project_id, kept + new_records, repo_root=repo)
    return new_records


def has_blocking_citations(project_id: str, *, repo_root: Path | None = None) -> bool:
    """Return True iff the project has any unreachable or mismatch citations.

    This is the gate the Advancement-Evaluator consults at the
    research_review → research_accepted and paper_review → paper_accepted
    transitions.
    """
    cits = citations_store.load(project_id, repo_root=repo_root)
    return any(
        c.verification_status in {VerificationStatus.UNREACHABLE, VerificationStatus.MISMATCH}
        for c in cits
    )


def project_has_unverified_for_review(project: Project, *, repo_root: Path | None = None) -> bool:
    """FIX C2: applied by Advancement-Evaluator before awarding any review point.

    Returns True if the project's reviewed artifacts contain any
    citation that did not pass verification. Identical semantics to
    has_blocking_citations() but accepts a Project for ergonomics.
    """
    return has_blocking_citations(project.id, repo_root=repo_root)


__all__ = [
    "ExtractedCitation",
    "extract_citations",
    "has_blocking_citations",
    "project_has_unverified_for_review",
    "validate_artifact",
]
