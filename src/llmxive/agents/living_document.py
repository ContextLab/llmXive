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
from collections.abc import Callable
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
    backend: object | None = None,
    model: str = "qwen.qwen3.5-122b",
) -> IngestResult:
    """Ingest one post-``posted`` comment.

    Routes ``comment_text`` through ``triage_submission`` with stage
    ``"posted"`` + the paper-review lens set (so the triage is
    cross-checked against the same 12-panel lenses the paper was
    originally reviewed under). Preserved comments are appended to the
    project's living log; rejected comments produce a no-op
    :class:`IngestResult` carrying the triage reason.

    When ``backend`` is provided, the triage uses the LLM-based intent
    classifier from :mod:`llmxive.convergence.triage` (recommended for
    production); falls back to the keyword matcher when ``backend`` is
    None (for tests + offline diagnostic use).
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
    judge = None
    if backend is not None:
        from llmxive.convergence.triage import llm_topic_judge
        judge = llm_topic_judge(backend, model=model)
    record = triage_submission(
        comment_text,
        source="human" if source not in {"human", "personality"} else source,  # type: ignore[arg-type]
        author=author,
        stage=stage,
        lenses=lenses,
        judge_fn=judge,
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


# --- paper-source Discussion write (FR-048) ------------------------------

# The rendered Discussion section is written into a DEDICATED managed
# include file (mirroring the publisher's ``_llmxive_appendix.tex``
# convention) and pulled into the primary tex via ``\input{...}`` placed
# just before ``\end{document}``. This is intentionally non-destructive:
# it never clobbers an author-authored ``\section{Discussion}`` already in
# the body, and a batched recompile only ever rewrites THIS managed file —
# so it can never block or rewind current progress (FR-048).
_DISCUSSION_INCLUDE = "_llmxive_discussion.tex"


def project_paper_source_dir(project_dir: Path) -> Path:
    """The paper LaTeX source directory (``paper/source``)."""
    return project_dir / "paper" / "source"


def _find_primary_tex(source_dir: Path) -> Path | None:
    """Locate the primary tex (the one carrying ``\\documentclass``).

    Same heuristic the publisher uses (:func:`llmxive.agents.publisher._find_primary_tex`)
    so both agents agree on which file is canonical."""
    if not source_dir.is_dir():
        return None
    for tex in sorted(source_dir.rglob("*.tex")):
        if tex.name == _DISCUSSION_INCLUDE:
            continue
        try:
            head = tex.read_text(encoding="utf-8", errors="ignore")[:4000]
        except OSError:
            continue
        if "\\documentclass" in head:
            return tex
    return None


def write_discussion_to_paper_source(
    project_dir: Path, render: DiscussionRender,
) -> Path | None:
    """Write ``render.section_text`` into the managed Discussion include
    and ensure the primary tex ``\\input``s it before ``\\end{document}``.

    Returns the include path that was written, or ``None`` if no primary
    tex (with ``\\documentclass``) could be located under ``paper/source``
    (a paper that has not yet been compiled — nothing to update)."""
    source_dir = project_paper_source_dir(project_dir)
    primary = _find_primary_tex(source_dir)
    if primary is None:
        return None
    include_path = source_dir / _DISCUSSION_INCLUDE
    include_path.parent.mkdir(parents=True, exist_ok=True)
    include_path.write_text(render.section_text + "\n", encoding="utf-8")
    # Idempotently ensure the primary tex inputs the managed include.
    text = primary.read_text(encoding="utf-8")
    marker = f"\\input{{{_DISCUSSION_INCLUDE}}}"
    if marker not in text and r"\end{document}" in text:
        text = text.replace(
            r"\end{document}", f"{marker}\n\\end{{document}}", 1,
        )
        primary.write_text(text, encoding="utf-8")
    return include_path


# --- batched recompile orchestrator (FR-048) -----------------------------


def project_memory_dir(project_dir: Path) -> Path:
    """The per-project speckit memory dir holding the FR-054 sign-off."""
    return project_dir / ".specify" / "memory"


@dataclass(frozen=True)
class RecompileResult:
    """Outcome of one :func:`run_batched_recompile` invocation."""

    ran: bool
    discussion_updated: bool = False
    material_change: bool = False
    version_doi_minted: bool = False
    awaiting_signoff: bool = False
    reason: str = ""


# A mint hook is injected so the network boundary (Zenodo) stays out of
# the orchestrator. It receives the project_dir + repo_root + the digest
# being published and performs the real version-DOI mint (publisher
# version path). When ``None``, the orchestrator NEVER mints — it only
# renders + detects material change + stages for sign-off (the cron
# auto-trigger uses this no-mint mode so the version DOI always pauses at
# the FR-054 manual sign-off).
MintVersionDoi = Callable[..., object]


def run_batched_recompile(
    project_dir: Path,
    *,
    backend: object | None = None,
    repo_root: Path,
    mint_version_doi: MintVersionDoi | None = None,
) -> RecompileResult:
    """Consume the recompile queue → render the Discussion into the paper
    source → decide whether the change is material → (only when signed
    off + a mint hook is supplied) mint a new Zenodo version DOI.

    This is the FR-048 orchestrator. It ties together the previously
    free-standing helpers (:func:`render_discussion_section`,
    :func:`should_mint_version_doi`, :func:`commit_digest`,
    :func:`clear_recompile_queue`) and reuses the EXISTING FR-054
    sign-off gate (:func:`llmxive.speckit._publication_signoff.has_signoff`)
    — no parallel gate is invented.

    Decision table:
    - empty queue → no-op (``ran=False``).
    - non-material (digest unchanged) → render is applied, queue cleared,
      digest re-committed, no DOI.
    - material + NO sign-off → render is applied, queue + digest LEFT
      INTACT (so a later signed run can mint), ``awaiting_signoff=True``.
    - material + signed off + ``mint_version_doi`` supplied → mint, then
      commit digest + clear queue, ``version_doi_minted=True``.
    - material + signed off + NO mint hook (cron auto-trigger) → render
      applied, queue/digest LEFT INTACT, ``awaiting_signoff`` False but
      not minted (a maintainer-run mint completes it).

    The render is non-destructive (writes a managed include only), so it
    cannot block or rewind current progress (FR-048).
    """
    from llmxive.speckit._publication_signoff import has_signoff

    if pending_recompile_count(project_dir) == 0:
        return RecompileResult(ran=False, reason="no queued comments")

    render = render_discussion_section(project_dir)
    write_discussion_to_paper_source(project_dir, render)

    should_mint, mint_reason = should_mint_version_doi(project_dir)
    if not should_mint:
        # Cosmetic / non-material recompile: clear the queue + re-commit
        # the (unchanged) digest. No DOI version slot is burned.
        clear_recompile_queue(project_dir)
        commit_digest(project_dir, render.digest)
        return RecompileResult(
            ran=True,
            discussion_updated=True,
            material_change=False,
            reason=mint_reason,
        )

    # Material change — gated by the FR-054 maintainer sign-off.
    if not has_signoff(project_memory_dir(project_dir)):
        # Stage for sign-off: leave the queue + previous digest INTACT so
        # a later signed run re-detects the material change and mints.
        return RecompileResult(
            ran=True,
            discussion_updated=True,
            material_change=True,
            awaiting_signoff=True,
            reason=(
                "material Discussion change awaiting FR-054 maintainer "
                f"sign-off; run `llmxive project publish-approve` ({mint_reason})"
            ),
        )

    if mint_version_doi is None:
        # Signed off but no mint hook (cron auto-trigger path): the render
        # is applied + material change detected, but the actual Zenodo
        # mint is left to a maintainer-driven run. Queue/digest preserved.
        return RecompileResult(
            ran=True,
            discussion_updated=True,
            material_change=True,
            awaiting_signoff=False,
            reason=(
                "material change + sign-off present, but no mint hook "
                f"supplied (auto-trigger does not mint) ({mint_reason})"
            ),
        )

    # Signed off + mint hook supplied → mint the version DOI, then commit
    # the digest + clear the queue so the next batch starts clean.
    mint_version_doi(
        project_dir=project_dir, repo_root=repo_root, digest=render.digest,
    )
    commit_digest(project_dir, render.digest)
    clear_recompile_queue(project_dir)
    return RecompileResult(
        ran=True,
        discussion_updated=True,
        material_change=True,
        version_doi_minted=True,
        reason=f"minted new version DOI ({mint_reason})",
    )


# --- off-topic vs on-topic --------------------------------------------


def is_off_topic(
    comment_text: str,
    *,
    lenses: list[str] | None = None,
    backend: object | None = None,
    model: str = "qwen.qwen3.5-122b",
) -> bool:
    """Convenience wrapper for the off-topic check used by the
    publisher's UI / GitHub-action layer to give an immediate
    yes/no answer without persisting.

    When ``backend`` is provided, the triage uses an LLM-based intent
    classifier (the same one ``ingest_comment`` uses for production
    triage); this is the recommended path for T079 verification
    because the LLM judge is robust to clever off-topic comments that
    happen to name-drop a lens. When ``backend`` is None, the triage
    falls back to the cheap keyword-matching path (suitable for tests
    + offline diagnostic probes).
    """
    if lenses is None:
        lenses = [
            "claim_accuracy", "logical_consistency", "statistical_analysis",
            "scientific_evidence", "figure_critic", "jargon_police",
            "overreach", "safety_ethics", "code_quality", "data_quality",
            "text_formatting", "writing_quality",
        ]
    judge = None
    if backend is not None:
        from llmxive.convergence.triage import llm_topic_judge
        judge = llm_topic_judge(backend, model=model)
    record = triage_submission(
        comment_text,
        source="human",
        author="<probe>",
        stage="posted",
        lenses=lenses,
        judge_fn=judge,
    )
    return not record.safe_on_topic


__all__ = [
    "DiscussionRender",
    "IngestResult",
    "RecompileResult",
    "clear_recompile_queue",
    "commit_digest",
    "digest_path",
    "ingest_comment",
    "is_off_topic",
    "pending_recompile_count",
    "previous_digest",
    "project_living_dir",
    "project_log_path",
    "project_memory_dir",
    "project_paper_source_dir",
    "project_queue_path",
    "render_discussion_section",
    "run_batched_recompile",
    "should_mint_version_doi",
    "write_discussion_to_paper_source",
]
