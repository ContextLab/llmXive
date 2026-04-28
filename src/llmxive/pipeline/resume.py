"""Resume-from-failure helper (T030).

Reads the latest run-log entry per project; if it failed, the next
scheduled run picks up from that stage rather than restarting the
project from brainstormed.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.state import runlog
from llmxive.types import Outcome, Project


def needs_resume(project: Project, *, repo_root: Path | None = None) -> bool:
    """True iff the project's last run failed mid-pipeline."""
    last = runlog.latest_for_project(project.id, repo_root=repo_root)
    if last is None:
        return False
    return last.outcome == Outcome.FAILED


def last_failed_agent(project: Project, *, repo_root: Path | None = None) -> str | None:
    last = runlog.latest_for_project(project.id, repo_root=repo_root)
    if last is None or last.outcome != Outcome.FAILED:
        return None
    return last.agent_name


__all__ = ["needs_resume", "last_failed_agent"]
