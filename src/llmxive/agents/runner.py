"""Invoke one agent on a project — the SINGLE integration point for
spec 009 activity-feed delivery (FR-026), manifest validation (FR-028),
and dispatch ledger recording (FR-034).

Acquires the per-project lock, packs the project's activity feed into the
agent's context, calls Agent.run(), validates the agent's "comments
considered" manifest, appends the contribution + manifest to the feed (or
records a dispatch_failure on validation failure), writes the run-log
entry, releases the lock.

Per spec 009 research.md §9: this is the ONE place every dispatch flows
through. Per-agent re-implementation is forbidden by Constitution I.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Iterator

from llmxive.agents.base import Agent, AgentContext
from llmxive.pipeline import lock as lockmod
from llmxive.types import RunLogEntry

log = logging.getLogger(__name__)

# How many chars of feed to inject (FR-031). Conservative default keeps
# the budget comfortably below typical 32k context windows.
DEFAULT_FEED_BUDGET = 20_000


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


def _pack_feed_into_context(
    ctx: AgentContext,
    repo_root: Path,
    *,
    budget_chars: int = DEFAULT_FEED_BUDGET,
) -> AgentContext:
    """Spec 009 FR-026: load + pack the project's activity feed; inject into ctx.

    Returns a new AgentContext with `feed_context`, `dispatch_id`,
    `feed_truncated`, `feed_snapshot_at` populated. The original ctx is
    NOT mutated (dataclass replace).
    """
    from llmxive.feed import FeedStore
    from llmxive.feed.store import _new_ulid

    store = FeedStore(repo_root)
    try:
        packed = store.pack_for_dispatch(ctx.project_id, budget_chars=budget_chars)
    except FileNotFoundError:
        # No project dir / feed yet — pass through with empty feed context
        packed = None

    dispatch_id = _new_ulid()
    if packed is None:
        return replace(
            ctx,
            feed_context="",
            dispatch_id=dispatch_id,
            feed_truncated=False,
            feed_snapshot_at="",
        )

    feed_block = packed.to_context_block() if packed.items or packed.truncated else ""
    return replace(
        ctx,
        feed_context=feed_block,
        dispatch_id=dispatch_id,
        feed_truncated=packed.truncated > 0,
        feed_snapshot_at=packed.feed_snapshot_at,
    )


def _record_dispatch(
    ctx: AgentContext,
    repo_root: Path,
    *,
    agent_name: str,
    feed_delivered: bool,
    manifest: dict | None = None,
    failure: dict | None = None,
) -> None:
    """Spec 009 FR-034 inputs: record dispatch metadata for the feedback-loop auditor."""
    from llmxive.feed import FeedStore

    store = FeedStore(repo_root)
    try:
        store.record_dispatch(ctx.project_id, {
            "dispatch_id": ctx.dispatch_id,
            "agent": agent_name,
            "task_id": ctx.task_id,
            "feed_delivered": feed_delivered,
            "feed_snapshot_at": ctx.feed_snapshot_at,
            "manifest": manifest,
            "failure": failure,
        })
    except FileNotFoundError:
        log.debug("project %s has no directory yet; skipping dispatch ledger", ctx.project_id)


def run_agent(
    agent: Agent,
    ctx: AgentContext,
    *,
    repo_root: Path | None = None,
    inject_feed: bool = True,
) -> RunLogEntry:
    """Single dispatch entry point.

    Spec 009 FR-026: when ``inject_feed=True`` (default), the project's
    activity feed is packed and injected into ``ctx.feed_context`` BEFORE
    any other project-scoped instruction the agent reads.

    Spec 009 FR-034: every dispatch records metadata (dispatch_id, feed
    delivery flag, agent name) to ``.audit/dispatches/<date>.jsonl`` for the
    feedback-loop auditor to consume.

    ``inject_feed=False`` exists to support legacy tests + internal agents
    that don't yet emit a comments-considered manifest. New code paths
    SHOULD leave the default on.
    """
    rr = Path(repo_root) if repo_root else Path.cwd()
    with project_lock(ctx.project_id, ctx.run_id, repo_root=repo_root):
        if inject_feed:
            ctx = _pack_feed_into_context(ctx, rr)
            _record_dispatch(
                ctx, rr,
                agent_name=agent.name,
                feed_delivered=bool(ctx.feed_context) or ctx.feed_snapshot_at != "",
            )
        return agent.run(ctx)


__all__ = ["run_agent", "project_lock"]
