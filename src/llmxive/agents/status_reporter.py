"""Status-Reporter Agent (T118).

Runs at the end of every scheduled workflow. Most output is computed
deterministically from state files; the LLM is consulted only for the
narrative paragraph. Per FR-026 + FR-033 + FR-034 + FIX C5/C6:

  * regenerate web/data/projects.json (web-data schema)
  * post one GitHub issue comment per state transition
  * emit a workflow-summary YAML document
  * compute the 7-day rolling advancement-rate metric (SC-001)
  * compute the revision-round convergence distribution (SC-012)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from llmxive.agents import living_document
from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.config import STAGE_ADVANCEMENT_RATE_WINDOW_DAYS
from llmxive.config import repo_root as _repo_root
from llmxive.speckit.yaml_extract import parse_yaml_lenient
from llmxive.state import project as project_store


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _collect_run_metrics(repo: Path) -> dict[str, Any]:
    """Walk state/run-log and state/projects to compute the metrics."""
    state_dir = repo / "state"
    runlog_dir = state_dir / "run-log"
    projects = project_store.list_all(repo_root=repo)

    citations_verified = 0
    citations_blocked = 0
    cit_dir = state_dir / "citations"
    if cit_dir.is_dir():
        for cit_file in cit_dir.glob("PROJ-*.yaml"):
            try:
                cits = yaml.safe_load(cit_file.read_text(encoding="utf-8")) or []
            except yaml.YAMLError:
                continue
            for c in cits:
                status = (c or {}).get("verification_status")
                if status == "verified":
                    citations_verified += 1
                elif status in ("unreachable", "mismatch"):
                    citations_blocked += 1

    # Advancement rate over the configured window: count distinct
    # (project_id, project_id-current_stage) transitions in run-logs
    # whose `ended_at` falls inside the window.
    cutoff = datetime.now(UTC) - timedelta(days=STAGE_ADVANCEMENT_RATE_WINDOW_DAYS)
    advancements = 0
    paid_api_calls = 0
    if runlog_dir.is_dir():
        for month_dir in runlog_dir.iterdir():
            if not month_dir.is_dir() or month_dir.name.startswith("."):
                continue
            for jsonl in month_dir.glob("*.jsonl"):
                for line in jsonl.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    cost = entry.get("cost_estimate_usd", 0.0) or 0.0
                    if cost > 0:
                        paid_api_calls += 1
                    end_str = entry.get("ended_at")
                    if not end_str:
                        continue
                    try:
                        end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                    if end_dt >= cutoff and entry.get("outcome") == "success":
                        advancements += 1

    revision_distribution: dict[str, int] = {str(i): 0 for i in range(1, 6)}
    for project in projects:
        # Look at the project's tasker_rounds.yaml under specs/*/.specify/.
        # The Tasker writes rounds_used after a clean analyze report.
        for fid in (project.speckit_research_dir, project.speckit_paper_dir):
            if not fid:
                continue
            rounds_file = (
                repo
                / Path(fid).parent.parent
                / ".specify"
                / "memory"
                / "tasker_rounds.yaml"
            )
            if not rounds_file.exists():
                continue
            try:
                rounds_doc = yaml.safe_load(rounds_file.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue
            n = rounds_doc.get("rounds_used")
            if isinstance(n, int) and 1 <= n <= 5:
                revision_distribution[str(n)] = revision_distribution.get(str(n), 0) + 1

    return {
        "advancement_rate_7d": float(advancements),
        "paid_api_calls": paid_api_calls,
        "citations_verified": citations_verified,
        "citations_blocked": citations_blocked,
        "revision_round_distribution": revision_distribution,
    }


def run_living_document_recompiles(*, repo_root: Path) -> list[str]:
    """FR-048 auto-trigger: scan every ``posted`` project and run a
    batched recompile for any with queued post-publication comments.

    This is invoked on every cron tick (via :func:`regenerate_web_data`,
    which every pipeline workflow runs at end-of-tick). For each posted
    project with ``pending_recompile_count > 0`` it renders the updated
    Discussion section into the paper source and detects whether the
    change is material. It deliberately passes NO mint hook to
    :func:`run_batched_recompile`, so the version DOI ALWAYS pauses at the
    FR-054 manual sign-off — the auto-trigger never mints (per the chosen
    AUTO-TRIGGER-but-manual-DOI policy).

    Defensive: a recompile failure for one project is logged and skipped;
    it must not break the cron tick for the others. Returns the list of
    project ids that were (attempted to be) recompiled, for telemetry.
    """
    from llmxive.types import Stage

    recompiled: list[str] = []
    try:
        projects = project_store.list_all(repo_root=repo_root)
    except Exception as exc:  # pragma: no cover — telemetry only
        print(f"[status_reporter] could not list projects for recompile: {exc}")
        return recompiled
    for project in projects:
        if project.current_stage != Stage.POSTED:
            continue
        project_dir = repo_root / "projects" / project.id
        try:
            if living_document.pending_recompile_count(project_dir) == 0:
                continue
            result = living_document.run_batched_recompile(
                project_dir, repo_root=repo_root, mint_version_doi=None,
            )
            if result.ran:
                recompiled.append(project.id)
        except Exception as exc:  # pragma: no cover — telemetry only
            print(
                f"[status_reporter] living-document recompile failed for "
                f"{project.id}: {type(exc).__name__}: {exc}"
            )
            continue
    return recompiled


def regenerate_web_data(*, repo_root: Path | None = None) -> Path:
    """Write web/data/projects.json from current project state.

    Emits the v2 schema (specs/002-website-integration/contracts/web-data-v2.schema.yaml)
    via :mod:`llmxive.web_data`. The v1 contract is preserved in
    specs/001 for back-compat but is no longer the writer's target.

    Also fires the FR-048 living-document auto-trigger
    (:func:`run_living_document_recompiles`) so posted papers with queued
    post-publication comments get their Discussion section recompiled on
    every cron tick. The version DOI still pauses at the FR-054 manual
    sign-off (the auto-trigger never mints).
    """
    from llmxive import web_data

    repo = repo_root or _repo_root()
    # Fire the living-document recompile auto-trigger BEFORE rebuilding the
    # web payload, so any Discussion-source updates are reflected. Wrapped
    # so a recompile fault can never block web-data regeneration.
    try:
        run_living_document_recompiles(repo_root=repo)
    except Exception as exc:  # pragma: no cover — telemetry only
        print(f"[status_reporter] living-document auto-trigger faulted: {exc}")
    return web_data.write_payload(repo)


class StatusReporterAgent(Agent):
    """End-of-run summary writer + web/data regenerator."""

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = _repo_root()
        metrics = _collect_run_metrics(repo)
        # Cache metrics on ctx for handle_response to reuse.
        ctx.metadata["_metrics_json"] = json.dumps(metrics, sort_keys=True)

        system = render_prompt(
            "agents/prompts/status_reporter.md",
            {"run_id": ctx.run_id},
            repo_root=repo,
        )
        user = (
            f"# run_id\n{ctx.run_id}\n\n"
            f"# metrics\n\n```yaml\n{yaml.safe_dump(metrics, sort_keys=True)}```\n\n"
            "# Task\n\nReturn the YAML status report per the contract."
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        repo = _repo_root()

        # Regenerate web/data/projects.json regardless of LLM output.
        web_data_path = regenerate_web_data(repo_root=repo)

        # Persist the LLM narrative + metrics to a per-run summary file.
        try:
            doc = parse_yaml_lenient(response.text) or {}
        except yaml.YAMLError:
            doc = {}
        if not isinstance(doc, dict):
            doc = {}

        # Inject our deterministic metrics so they always reflect the
        # state files (not whatever the LLM hallucinates).
        try:
            metrics = json.loads(ctx.metadata.get("_metrics_json", "{}"))
        except json.JSONDecodeError:
            metrics = {}
        doc["metrics"] = metrics

        summary_dir = repo / "state" / "run-log" / "summaries"
        summary_dir.mkdir(parents=True, exist_ok=True)
        summary_path = summary_dir / f"{ctx.run_id}.yaml"
        summary_path.write_text(
            yaml.safe_dump(doc, sort_keys=True, allow_unicode=True),
            encoding="utf-8",
        )

        return [
            str(web_data_path.relative_to(repo)),
            str(summary_path.relative_to(repo)),
        ]


__all__ = [
    "StatusReporterAgent",
    "regenerate_web_data",
    "run_living_document_recompiles",
]
