"""Triage entry point for an externally-ingested paper (spec 024).

Called by the ``Stage.PAPER_INGESTED`` graph handler for one project. Classifies
the paper and dispatches to the code-included or no-code branch, each of which
transforms the bare ingested project into a normal pipeline project (writing all
artifacts to disk + returning the project with its new ``current_stage``). The
caller persists the returned project and commits.
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
