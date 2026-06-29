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


def reprocess_ingested_paper(project: Project, *, repo_root: Path | None = None) -> Project:
    """Triage one ingested paper into the pipeline.

    code-included -> :func:`branch_code.to_backfilled_project`
    no-code       -> :func:`branch_nocode.to_followup_idea`

    Returns the transformed project (its ``current_stage`` is now a normal
    pipeline stage: ``in_progress`` for a runnable code paper, else
    ``brainstormed``). Raises on a genuinely un-triageable paper (the caller's
    per-project failsafe records it; we never silently no-op).
    """
    repo = repo_root or _repo_root()
    pdir = project_dir(project, repo)

    from llmxive.paper_reprocess.classify import classify_paper

    if classify_paper(pdir) == "code":
        from llmxive.paper_reprocess.branch_code import to_backfilled_project

        return to_backfilled_project(project, repo_root=repo)

    from llmxive.paper_reprocess.branch_nocode import to_followup_idea

    return to_followup_idea(project, repo_root=repo)
