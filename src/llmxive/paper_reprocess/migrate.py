"""One-time-general migration of stranded ingested papers (spec 024).

Before spec 024, intake dumped externally-ingested papers at ``paper_review``,
where they froze (the authored-paper revise loop has nothing to revise on a
third-party paper). This moves every such *unprocessed external* paper to
``paper_ingested`` so the reprocessor triages it into the real pipeline.

The predicate is GENERAL and SELF-GUARDING — it can run repeatedly and will
never touch an llmXive-AUTHORED paper that legitimately reaches ``paper_review``:
such a paper went through the research Spec Kit pipeline (so ``speckit_research_dir``
is set) and has no externally-ingested ``arxiv_id``. Only a bare external intake
(``arxiv_id`` present, ``speckit_research_dir`` unset) matches.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from llmxive.config import repo_root as _repo_root
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


def is_unprocessed_external_paper(project: Project, project_dir: Path) -> bool:
    """True iff ``project`` is a bare externally-ingested paper stranded at
    ``paper_review`` (never ran through our research pipeline)."""
    if project.current_stage != Stage.PAPER_REVIEW:
        return False
    if project.speckit_research_dir:  # an authored paper that ran the pipeline
        return False
    meta = project_dir / "paper" / "metadata.json"
    if not meta.is_file():
        return False
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return bool(isinstance(data, dict) and data.get("arxiv_id"))


def migrate_unprocessed_external_papers(
    *, repo_root: Path | None = None, dry_run: bool = False
) -> list[str]:
    """Move every stranded external paper from ``paper_review`` -> ``paper_ingested``.

    Idempotent. Returns the list of migrated project ids (what WOULD migrate when
    ``dry_run``). Persists each change individually (small commits, no big-bang).
    """
    repo = repo_root or _repo_root()
    from llmxive.paper_reprocess.reprocess import project_dir

    migrated: list[str] = []
    for project in project_store.list_all(repo_root=repo):
        pdir = project_dir(project, repo)
        if not is_unprocessed_external_paper(project, pdir):
            continue
        migrated.append(project.id)
        if dry_run:
            continue
        moved = project.model_copy(update={
            "current_stage": Stage.PAPER_INGESTED,
            "updated_at": datetime.now(UTC),
        })
        project_store.save(moved, repo_root=repo)
    return migrated
