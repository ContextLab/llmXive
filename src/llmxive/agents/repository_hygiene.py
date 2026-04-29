"""Repository-Hygiene Agent (T120).

Read-only. Walks the repo for hygiene violations + computes the
SC-007 line-count delta against `state/migration_metrics.yaml`. The
LLM is consulted only to produce a one-paragraph narrative.

Stage transitions: none.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse


@dataclass
class HygieneFlag:
    kind: str
    severity: str
    summary: str
    suggested_fix: str


REQUIRED_GITIGNORE = (
    ".env",
    ".env.*",
    ".venv",
    "state/run-log/*/in-progress/",
    "state/run-log/*/.invalid/",
)


def _check_gitignore(repo: Path) -> list[HygieneFlag]:
    gitignore = repo / ".gitignore"
    if not gitignore.exists():
        return [
            HygieneFlag(
                kind="missing_gitignore",
                severity="critical",
                summary=".gitignore is missing at repo root",
                suggested_fix="create .gitignore with the project's required patterns",
            )
        ]
    text = gitignore.read_text(encoding="utf-8")
    flags: list[HygieneFlag] = []
    for pattern in REQUIRED_GITIGNORE:
        if pattern not in text:
            flags.append(
                HygieneFlag(
                    kind="missing_gitignore_pattern",
                    severity="medium",
                    summary=f".gitignore missing required pattern: {pattern}",
                    suggested_fix=f"append `{pattern}` to .gitignore",
                )
            )
    return flags


def _check_leftover_artifacts(repo: Path) -> list[HygieneFlag]:
    """Catch scratch artifacts at repo root that should not be committed."""
    flags: list[HygieneFlag] = []
    for name in ("pipeline_log.txt", "=", "scratch.txt", "tmp.txt"):
        candidate = repo / name
        if candidate.exists():
            flags.append(
                HygieneFlag(
                    kind="leftover_artifact",
                    severity="low",
                    summary=f"scratch artifact at repo root: {name}",
                    suggested_fix=f"delete {name} or move it to a documented location",
                )
            )
    # Stray .png files at repo root (allowed under web/assets/).
    for png in repo.glob("*.png"):
        flags.append(
            HygieneFlag(
                kind="leftover_screenshot",
                severity="low",
                summary=f"screenshot at repo root: {png.name}",
                suggested_fix=f"delete {png.name} or move it under web/assets/",
            )
        )
    return flags


def _count_lines(directory: Path) -> int:
    if not directory.is_dir():
        return 0
    total = 0
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        if any(p.startswith(".") and p != "." for p in path.parts):
            continue
        try:
            total += sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    return total


def _check_loc_metric(repo: Path) -> tuple[list[HygieneFlag], dict[str, Any]]:
    """SC-007 line-count assertion (FIX C3)."""
    metric_path = repo / "state" / "migration_metrics.yaml"
    baseline: int | None = None
    if metric_path.exists():
        try:
            doc = yaml.safe_load(metric_path.read_text(encoding="utf-8")) or {}
            baseline = doc.get("legacy_automation_loc")
            if not isinstance(baseline, int):
                baseline = None
        except yaml.YAMLError:
            baseline = None

    current = _count_lines(repo / "src" / "llmxive") + _count_lines(repo / "agents")
    flags: list[HygieneFlag] = []
    if baseline is not None and current >= baseline:
        flags.append(
            HygieneFlag(
                kind="loc_regression",
                severity="high",
                summary=(
                    f"SC-007 regression: post-migration LOC ({current}) >= baseline ({baseline})"
                ),
                suggested_fix=(
                    "investigate which new modules added unnecessary lines; "
                    "consolidate per Constitution Principle I"
                ),
            )
        )
    metric = {
        "baseline": baseline,
        "current": current,
        "reduction": (baseline - current) if baseline is not None else 0,
        "status": (
            "no-baseline"
            if baseline is None
            else ("ok" if current < baseline else "regression")
        ),
    }
    return flags, metric


class RepositoryHygieneAgent(Agent):
    """Read-only hygiene checker. Persists flag list to state."""

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        flags = _check_gitignore(repo) + _check_leftover_artifacts(repo)
        loc_flags, loc_metric = _check_loc_metric(repo)
        flags.extend(loc_flags)

        ctx.metadata["_flags_json"] = json.dumps([asdict(f) for f in flags])
        ctx.metadata["_loc_metric_json"] = json.dumps(loc_metric)

        system = render_prompt(
            "agents/prompts/repository_hygiene.md",
            {"run_id": ctx.run_id},
            repo_root=repo,
        )
        user = (
            f"# Flags (deterministic)\n\n```json\n{ctx.metadata['_flags_json']}\n```\n\n"
            f"# Line-count metric\n\n```json\n{ctx.metadata['_loc_metric_json']}\n```\n\n"
            "# Task\n\nReturn the YAML report per the contract."
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        try:
            doc = yaml.safe_load(response.text) or {}
        except yaml.YAMLError:
            doc = {}
        if not isinstance(doc, dict):
            doc = {}

        # Always inject our deterministic flags + metric (LLM may
        # paraphrase but the source of truth is the runtime).
        try:
            doc["flags"] = json.loads(ctx.metadata.get("_flags_json", "[]"))
        except json.JSONDecodeError:
            doc["flags"] = []
        try:
            doc["loc_metric"] = json.loads(ctx.metadata.get("_loc_metric_json", "{}"))
        except json.JSONDecodeError:
            doc["loc_metric"] = {}
        if not doc.get("verdict"):
            doc["verdict"] = "clean" if not doc["flags"] else "flagged"

        report_path = repo / "state" / "run-log" / "hygiene" / f"{ctx.run_id}.yaml"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(yaml.safe_dump(doc, sort_keys=True), encoding="utf-8")
        return [str(report_path.relative_to(repo))]


__all__ = ["RepositoryHygieneAgent"]
