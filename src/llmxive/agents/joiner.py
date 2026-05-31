"""Task-Joiner Agent (T124).

Auto-spawned when every sibling sub-task in an atomized set has
outcome=success in the run-log. Merges sub-task outputs into the
parent task's expected artifact format. Supports hierarchical merges
(level-N Joiner output becomes input to level-(N-1) Joiner).

The Joiner emits a single run-log entry that lists every sibling's
task_id in its `inputs` field, preserving the atomization tree's
audit trail.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.config import repo_root as _repo_root
from llmxive.speckit.yaml_extract import parse_yaml_lenient


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _gather_atomization_tree(project_id: str, parent_task_id: str, *, repo_root: Path) -> dict[str, object] | None:
    """Walk the project's .tasks/ dir to find this parent's atomize doc."""
    project_dir = repo_root / "projects" / project_id
    for sub in (project_dir / "code" / ".tasks", project_dir / "paper" / "source" / ".tasks"):
        candidate = sub / f"{parent_task_id}.atomize.yaml"
        if candidate.exists():
            try:
                return yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue
    return None


class TaskJoinerAgent(Agent):
    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = _repo_root()
        parent_task_id = ctx.metadata.get("parent_task_id", ctx.task_id)
        tree = _gather_atomization_tree(
            ctx.project_id, parent_task_id, repo_root=repo
        ) or {}
        _st = tree.get("sub_tasks")
        sub_tasks: list[dict[str, object]] = _st if isinstance(_st, list) else []

        # Read the actual outputs from each sub-task by listing files in
        # the project tree (the sub-task agents already wrote them).
        sibling_outputs: list[dict[str, object]] = []
        for sub in sub_tasks:
            sibling_outputs.append(
                {
                    "task_id": sub.get("task_id"),
                    "outputs": sub.get("expected_outputs", []),
                }
            )

        _peo = ctx.metadata.get("parent_expected_outputs", "")
        parent_expected_outputs: list[str] = [_peo] if _peo else []

        system = render_prompt(
            "agents/prompts/task_joiner.md",
            {"project_id": ctx.project_id, "parent_task_id": parent_task_id},
            repo_root=repo,
        )
        user = (
            f"# parent_task_id\n{parent_task_id}\n\n"
            f"# parent_expected_outputs\n{parent_expected_outputs}\n\n"
            f"# sibling_outputs\n\n```yaml\n{yaml.safe_dump(sibling_outputs)}\n```\n\n"
            "Return the YAML merge document per the contract."
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        repo = _repo_root()
        try:
            doc = parse_yaml_lenient(response.text)
        except yaml.YAMLError as exc:
            raise RuntimeError(f"Joiner returned invalid YAML: {exc}") from exc
        if not isinstance(doc, dict) or doc.get("verdict") != "merged":
            return []

        written: list[str] = []
        _pe = ctx.metadata.get("parent_expected_outputs", "")
        parent_expected: list[str] = [_pe] if _pe else []
        for merged in doc.get("merged_outputs", []) or []:
            relpath = merged.get("path")
            contents = merged.get("contents", "")
            if not relpath:
                continue
            if parent_expected and relpath not in parent_expected:
                # Per the contract, the Joiner MUST NOT modify files
                # outside the parent's expected outputs.
                continue
            target = repo / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(contents, encoding="utf-8")
            written.append(relpath)
        return written


__all__ = ["TaskJoinerAgent"]
