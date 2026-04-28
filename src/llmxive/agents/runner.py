"""Invoke one agent on a project (T024).

Acquires the per-project lock, calls Agent.run() (or a Spec-Kit-driving
agent's run()), writes the run-log entry, releases the lock.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from llmxive.agents.base import Agent, AgentContext
from llmxive.pipeline import lock as lockmod
from llmxive.types import RunLogEntry


@contextmanager
def project_lock(project_id: str, holder_run_id: str, *, ttl_seconds: int = 3600,
                 repo_root: Path | None = None) -> Iterator[None]:
    lockmod.acquire(
        project_id,
        holder_run_id=holder_run_id,
        ttl_seconds=ttl_seconds,
        repo_root=repo_root,
    )
    try:
        yield
    finally:
        lockmod.release(project_id, holder_run_id=holder_run_id, repo_root=repo_root)


def run_agent(agent: Agent, ctx: AgentContext, *, repo_root: Path | None = None) -> RunLogEntry:
    with project_lock(ctx.project_id, ctx.run_id, repo_root=repo_root):
        return agent.run(ctx)


__all__ = ["run_agent", "project_lock"]
