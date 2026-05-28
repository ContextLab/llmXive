"""Post-`posted` living-document module (spec 015 T077/T078).

Once a paper enters the ``posted`` stage, comments left on it
(GitHub issue comments, personality-cron contributions, etc.) are no
longer dropped — they flow through this module, which:

1. **Ingests** each incoming comment via
   :func:`llmxive.convergence.triage.triage_submission` (T077; FR-021/022 —
   quality + safety + on-topic gates).
2. **Persists** preserved comments to a per-project log
   (``projects/<id>/paper/living_document/log.jsonl``).
3. **Batches** comments into a recompile queue keyed by project; the
   queue is consumed by the publisher when the maintainer triggers a
   batched recompile.
4. **Renders** an updated Discussion section into the paper source by
   appending each preserved comment under headed sub-sections
   (T078).
5. **Detects** whether the PDF MATERIALLY changed (i.e., the rendered
   Discussion section's content tokens differ from the previous
   compile) — only THEN does the publisher mint a NEW Zenodo version
   DOI, gated by the FR-054 maintainer sign-off (same gate as initial
   publication).

The publisher invokes :func:`should_mint_version_doi` BEFORE asking
Zenodo for a new version — so a non-material recompile (e.g.
formatting-only fix) doesn't burn a DOI version slot.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from llmxive.convergence.triage import triage_submission
from llmxive.convergence.types import TriageRecord

# --- on-disk layout -------------------------------------------------------


def project_living_dir(project_dir: Path) -> Path:
    """Return the per-project living-document directory.
    Created on first write; no side effect on read paths."""
    return project_dir / "paper" / "living_document"


def project_log_path(project_dir: Path) -> Path:
    return project_living_dir(project_dir) / "log.jsonl"


def project_queue_path(project_dir: Path) -> Path:
    return project_living_dir(project_dir) / "recompile_queue.json"


# --- ingestion ------------------------------------------------------------


@dataclass(frozen=True)
class IngestResult:
    """Outcome of a single comment ingestion."""

    triage: TriageRecord
    persisted: bool
    log_path: Path | None
    """``None`` iff ``persisted=False``."""
    excluded_reason: str | None


def ingest_comment(
    *,
    project_dir: Path,
    comment_text: str,
    author: str,
    source: str = "human",
    stage: str = "posted",
    lenses: list[str] | None = None,
) -> IngestResult:
    """Ingest one post-``posted`` comment.

    Routes ``comment_text`` through ``triage_submission`` with stage
    ``"posted"`` + the paper-review lens set (so the triage is
    cross-checked against the same 12-panel lenses the paper was
    originally reviewed under). Preserved comments are appended to the
    project's living log; rejected comments produce a no-op
    :class:`IngestResult` carrying the triage reason.
    """
    if lenses is None:
        # Default to the paper-review panel's lens set (same as
        # personality.py's _PAPER_REVIEW_LENSES).
        lenses = [
            "claim_accuracy", "logical_consistency", "statistical_analysis",
            "scientific_evidence", "figure_critic", "jargon_police",
            "overreach", "safety_ethics", "code_quality", "data_quality",
            "text_formatting", "writing_quality",
        ]
    record = triage_submission(
        comment_text,
        source="human" if source not in {"human", "personality"} else source,  # type: ignore[arg-type]
        author=author,
        stage=stage,
        lenses=lenses,
    )
    if not record.preserved:
        return IngestResult(
            triage=record,
            persisted=False,
            log_path=None,
            excluded_reason=record.excluded_reason,
        )
    log_path = project_log_path(project_dir)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "author": author,
        "source": source,
        "stage_when_ingested": stage,
        "text": comment_text,
        "mapped_lenses": list(record.mapped_lenses),
        "ingested_at": datetime.now(UTC).isoformat(),
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    _enqueue_recompile(project_dir)
    return IngestResult(
        triage=record, persisted=True, log_path=log_path, excluded_reason=None,
    )


def _enqueue_recompile(project_dir: Path) -> None:
    """Add the project to its own recompile queue (the publisher
    consumes this when the maintainer triggers a batched recompile)."""
    qp = project_queue_path(project_dir)
    qp.parent.mkdir(parents=True, exist_ok=True)
    state: dict[str, int]
    if qp.exists():
        state = json.loads(qp.read_text())
    else:
        state = {"pending_comments": 0}
    state["pending_comments"] = state.get("pending_comments", 0) + 1
    state["last_enqueued_at"] = datetime.now(UTC).isoformat()  # type: ignore[assignment]
    qp.write_text(json.dumps(state, indent=2) + "\n")


def pending_recompile_count(project_dir: Path) -> int:
    """Number of preserved comments queued for the next batched recompile."""
    qp = project_queue_path(project_dir)
    if not qp.exists():
        return 0
    return int(json.loads(qp.read_text()).get("pending_comments", 0))


def clear_recompile_queue(project_dir: Path) -> None:
    """The publisher calls this AFTER a successful batched recompile
    + version-DOI mint, so the queue resets to 0."""
    qp = project_queue_path(project_dir)
    if qp.exists():
        qp.write_text(
            json.dumps(
                {"pending_comments": 0,
                 "last_cleared_at": datetime.now(UTC).isoformat()},
                indent=2,
            ) + "\n"
        )


# --- Discussion section render -------------------------------------------


@dataclass
class DiscussionRender:
    """Output of :func:`render_discussion_section`."""

    section_text: str
    """The full ``\\section{Discussion}`` body for inclusion in the
    paper's LaTeX source."""
    digest: str
    """A content digest used by :func:`should_mint_version_doi` to
    detect material PDF changes."""
    entries_consumed: int
    """How many log entries were rendered into the section."""


def render_discussion_section(project_dir: Path) -> DiscussionRender:
    """Read the project's living log + render an updated Discussion
    section. Returns a :class:`DiscussionRender` with the section text +
    a content digest the publisher uses to detect material changes.

    The render is intentionally simple: one subsection per preserved
    comment, with the author + ingestion date in the heading. The
    publisher inserts (or replaces) this section in the paper LaTeX
    source before recompiling.
    """
    log_path = project_log_path(project_dir)
    entries: list[dict[str, object]] = []
    if log_path.exists():
        for line in log_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # skip malformed line; honest-skip + log

    if not entries:
        section_text = (
            r"\section{Discussion}" + "\n\n"
            "% No post-publication discussion comments have been "
            "preserved yet.\n"
        )
    else:
        parts = [r"\section{Discussion}", ""]
        for i, e in enumerate(entries, start=1):
            author = str(e.get("author", "anon"))
            ingested = str(e.get("ingested_at", ""))[:10]  # YYYY-MM-DD
            text = str(e.get("text", "")).strip()
            parts.append(rf"\subsection{{Comment {i} ({author}, {ingested})}}")
            parts.append("")
            parts.append(text)
            parts.append("")
        section_text = "\n".join(parts)

    # Digest = sha256 of every author + text pair. Stable under
    # cosmetic re-rendering; sensitive to actual content changes.
    h = hashlib.sha256()
    for e in entries:
        h.update(str(e.get("author", "")).encode("utf-8"))
        h.update(b"\x00")
        h.update(str(e.get("text", "")).encode("utf-8"))
        h.update(b"\x01")
    return DiscussionRender(
        section_text=section_text,
        digest=h.hexdigest(),
        entries_consumed=len(entries),
    )


# --- Material PDF change detection ---------------------------------------


def digest_path(project_dir: Path) -> Path:
    return project_living_dir(project_dir) / "discussion_digest.txt"


def previous_digest(project_dir: Path) -> str | None:
    """The digest of the Discussion section from the LAST successful
    publish. Used to decide whether THIS recompile is material."""
    p = digest_path(project_dir)
    if not p.exists():
        return None
    return p.read_text().strip() or None


def should_mint_version_doi(project_dir: Path) -> tuple[bool, str]:
    """Decide whether a new Zenodo version DOI should be minted.

    Returns ``(should_mint, reason)``. The publisher uses this to gate
    its Zenodo-version call: if ``should_mint`` is False, the publisher
    SKIPs the DOI step (a non-material recompile doesn't burn a DOI
    version slot).

    The decision rule:
    - First recompile after initial publication AND any preserved
      comments exist → mint.
    - Subsequent recompile AND the Discussion digest CHANGED →
      mint.
    - Otherwise → skip.
    """
    render = render_discussion_section(project_dir)
    if render.entries_consumed == 0:
        return False, "no preserved comments → nothing material changed"
    prev = previous_digest(project_dir)
    if prev is None:
        return True, (
            f"first recompile after initial publication with "
            f"{render.entries_consumed} preserved comment(s)"
        )
    if prev != render.digest:
        return True, (
            f"Discussion digest changed (prev={prev[:12]}..., "
            f"new={render.digest[:12]}...; "
            f"{render.entries_consumed} comment(s) in log)"
        )
    return False, (
        "Discussion digest unchanged — recompile is cosmetic, "
        "no new DOI version required"
    )


def commit_digest(project_dir: Path, digest: str) -> None:
    """Record the digest as the new "previous digest" after a
    successful publish. The publisher calls this AFTER Zenodo confirms
    the version DOI."""
    p = digest_path(project_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(digest + "\n")


# --- off-topic vs on-topic --------------------------------------------


def is_off_topic(comment_text: str, *, lenses: list[str] | None = None) -> bool:
    """Convenience wrapper for the off-topic check used by the
    publisher's UI / GitHub-action layer to give an immediate
    yes/no answer without persisting. Mirrors triage's on-topic
    rule."""
    if lenses is None:
        lenses = [
            "claim_accuracy", "logical_consistency", "statistical_analysis",
            "scientific_evidence", "figure_critic", "jargon_police",
            "overreach", "safety_ethics", "code_quality", "data_quality",
            "text_formatting", "writing_quality",
        ]
    record = triage_submission(
        comment_text,
        source="human",
        author="<probe>",
        stage="posted",
        lenses=lenses,
    )
    return not record.safe_on_topic


__all__ = [
    "DiscussionRender",
    "IngestResult",
    "clear_recompile_queue",
    "commit_digest",
    "digest_path",
    "ingest_comment",
    "is_off_topic",
    "pending_recompile_count",
    "previous_digest",
    "project_living_dir",
    "project_log_path",
    "project_queue_path",
    "render_discussion_section",
    "should_mint_version_doi",
]
