"""Intake entry point for an externally-ingested paper (spec 024 + 2026-07-01 ethics).

Called by the ``Stage.PAPER_INGESTED`` graph handler for one project. Ethics
invariant (2026-07-01): an ingested third-party paper is NEVER modified.
:func:`reprocess_ingested_paper` marks it a review-only **Reviewed Preprint**
(writes ``paper/preprint.json`` provenance, preserves the original paper bytes +
authors, parks it terminal at ``REVIEWED_PREPRINT``);
:func:`finalize_reviewed_preprint` additionally runs the review-only panel once,
spawns a SEPARATE citing llmXive follow-up project, and records the follow-up id.
The caller persists the returned project and commits. The legacy in-place
``classify``/``branch_code``/``branch_nocode`` modify flow is retired from intake
(kept only for the one-time migration; see ``docs``/the design spec).
"""

from __future__ import annotations

from pathlib import Path

from llmxive.config import repo_root as _repo_root
from llmxive.types import Project


def project_dir(project: Project, repo_root: Path) -> Path:
    """Resolve a project's on-disk directory (the slug suffix is part of the
    directory name, e.g. ``projects/PROJ-640-https-arxiv-org-...``)."""
    exact = repo_root / "projects" / project.id
    if exact.is_dir():
        return exact
    matches = sorted((repo_root / "projects").glob(f"{project.id}*"))
    if matches:
        return matches[0]
    return exact  # let downstream raise a clear FileNotFoundError


def _load_intake_metadata(pdir: Path) -> dict:
    """Read ``paper/metadata.json`` (the arXiv/HF-parsed provenance). Empty on
    absence — the caller still marks the preprint; provenance fields degrade."""
    import json

    meta_path = pdir / "paper" / "metadata.json"
    if not meta_path.is_file():
        return {}
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def reprocess_ingested_paper(project: Project, *, repo_root: Path | None = None) -> Project:
    """Reviewed-Preprints ethics change (2026-07-01): NEVER modify an ingested paper.

    We have no consent to alter a third party's work, so intake no longer runs
    ``branch_code`` (which back-filled specs and revised the paper) nor transforms
    the project in place. Instead we mark the project a review-only **Reviewed
    Preprint**: write ``paper/preprint.json`` (provenance), preserve the original
    ``paper/`` bytes + ``metadata.json`` (original authors intact), and park it at
    the terminal ``REVIEWED_PREPRINT`` stage.

    The review artifacts (themed cover page + peer-review PDF + consolidated action
    items) and the SEPARATE llmXive brainstorm follow-up project are produced by the
    downstream review-only pipeline (``run_preprint_review`` / ``spawn_followup`` —
    additive, see the design spec); this triage only stops the modification and
    records the preprint. ``classify_paper`` / ``branch_code`` / ``branch_nocode``
    are retained for the migration + follow-up builder, not called from intake.
    """
    from datetime import UTC, datetime

    from llmxive.paper_reprocess.preprint import write_preprint_manifest
    from llmxive.types import Stage

    repo = repo_root or _repo_root()
    pdir = project_dir(project, repo)
    meta = _load_intake_metadata(pdir)

    write_preprint_manifest(
        pdir,
        source_url=str(meta.get("arxiv_url") or meta.get("source_url") or "").strip(),
        ingested_via=str(meta.get("submitted_via") or "").strip(),
        submitter=str(meta.get("submitter") or "").strip(),
        ingested_at=datetime.now(UTC).isoformat(),
    )
    return project.model_copy(update={"current_stage": Stage.REVIEWED_PREPRINT})


def finalize_reviewed_preprint(
    project: Project,
    *,
    repo_root: Path | None = None,
    run_id: str | None = None,
    spawn_followup: bool = True,
    review_agent_names: list[str] | None = None,
    _extension_fn=None,
) -> Project:
    """Full intake processing for one ingested paper (design spec §1).

    Three deterministic effects, in order, none of which touches the original:

    1. **Mark** it a Reviewed Preprint (:func:`reprocess_ingested_paper` — writes
       ``paper/preprint.json``, preserves the paper bytes + original authors,
       parks it terminal at ``REVIEWED_PREPRINT``).
    2. **Review** it once with the paper-review panel (peer-review feedback →
       ``paper/reviews/*`` + ``paper/action_items.md``; no accept/reject).
    3. **Spawn** a SEPARATE llmXive brainstorm follow-up project (our own study,
       which drops the original byline and CITES the source), recording its id in
       ``preprint.json::followup_project_id``.

    Returns the preprint project at ``REVIEWED_PREPRINT``. Review/spawn failures
    are non-fatal — the preprint is still marked + preserved, and the manifest
    records whatever follow-up id was obtained (``None`` on failure).

    Precondition: any prior llmXive ``*-llmxive.*`` modifications must already be
    stripped from ``paper/source`` (the migration does this) so the panel reviews
    the ORIGINAL work; a fresh intake has none.
    """
    import logging

    from llmxive.paper_reprocess.branch_nocode import spawn_followup_project
    from llmxive.paper_reprocess.preprint import (
        load_preprint_manifest,
        write_preprint_manifest,
    )
    from llmxive.paper_reprocess.preprint_review import run_preprint_review

    logger = logging.getLogger(__name__)
    repo = repo_root or _repo_root()
    marked = reprocess_ingested_paper(project, repo_root=repo)
    pdir = project_dir(project, repo)

    try:
        run_preprint_review(
            marked, repo_root=repo, run_id=run_id, agent_names=review_agent_names
        )
    except Exception as exc:  # review is advisory; never sink intake
        logger.warning("finalize_reviewed_preprint: review failed for %s: %s", project.id, exc)

    followup_id: str | None = None
    if spawn_followup:
        try:
            followup_id = spawn_followup_project(
                marked, repo_root=repo, _extension_fn=_extension_fn
            )
        except Exception as exc:  # a missing follow-up must not sink intake
            logger.warning(
                "finalize_reviewed_preprint: follow-up spawn failed for %s: %s",
                project.id, exc,
            )

    # Record the follow-up link, preserving the provenance the mark step wrote.
    existing = load_preprint_manifest(pdir) or {}
    write_preprint_manifest(
        pdir,
        source_url=str(existing.get("source_url") or "").strip(),
        ingested_via=str(existing.get("ingested_via") or "").strip(),
        submitter=str(existing.get("submitter") or "").strip(),
        ingested_at=str(existing.get("ingested_at") or "").strip(),
        followup_project_id=followup_id,
    )
    return marked
