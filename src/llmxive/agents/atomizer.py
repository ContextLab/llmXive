"""Task-Atomizer Agent (T122).

Decomposes an over-budget parent task into sub-tasks each fitting the
leaf wall-clock budget. Records the atomization tree under
`projects/<PROJ-ID>/code/.tasks/<task_id>.atomize.yaml` (research
stage) or `projects/<PROJ-ID>/paper/source/.tasks/<task_id>.atomize.yaml`
(paper stage). Hierarchical: a sub-task whose estimate still exceeds
the budget is re-atomized on the next scheduled run.

The agent's output records the sub-task tree; the parent task's
`run_log_entry.parent_entry_id` chain reconstructs the hierarchy.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import yaml

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.config import LEAF_TASK_BUDGET_SECONDS


MAX_ATOMIZATION_DEPTH = 4


class TaskAtomizerAgent(Agent):
    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        parent_task = ctx.metadata.get("parent_task", {})
        current_depth = int(ctx.metadata.get("current_depth", 0))

        system = render_prompt(
            "agents/prompts/task_atomizer.md",
            {
                "project_id": ctx.project_id,
                "leaf_budget_seconds": str(LEAF_TASK_BUDGET_SECONDS),
                "max_depth": str(MAX_ATOMIZATION_DEPTH),
                "current_depth": str(current_depth),
            },
            repo_root=repo,
        )
        user = (
            f"# parent_task\n\n```yaml\n{yaml.safe_dump(parent_task)}\n```\n\n"
            f"# leaf_budget_seconds\n{LEAF_TASK_BUDGET_SECONDS}\n\n"
            f"# current_depth\n{current_depth}\n\n"
            f"# max_depth\n{MAX_ATOMIZATION_DEPTH}\n\n"
            "Return the YAML decomposition per the contract."
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        try:
            doc = yaml.safe_load(response.text)
        except yaml.YAMLError as exc:
            raise RuntimeError(f"Atomizer returned invalid YAML: {exc}") from exc
        if not isinstance(doc, dict):
            raise RuntimeError("Atomizer YAML must be a mapping")

        # Assign UUIDs if the LLM didn't.
        for sub in doc.get("sub_tasks", []) or []:
            if not sub.get("task_id"):
                sub["task_id"] = str(uuid4())

        parent_task_id = doc.get("parent_task_id") or ctx.task_id
        # Decide the persistence directory by stage tag in metadata
        # (paper vs research). Default research.
        is_paper = ctx.metadata.get("stage") == "paper"
        if is_paper:
            base = repo / "projects" / ctx.project_id / "paper" / "source" / ".tasks"
        else:
            base = repo / "projects" / ctx.project_id / "code" / ".tasks"
        base.mkdir(parents=True, exist_ok=True)
        out_path = base / f"{parent_task_id}.atomize.yaml"
        out_path.write_text(
            yaml.safe_dump(doc, sort_keys=True, allow_unicode=True),
            encoding="utf-8",
        )
        return [str(out_path.relative_to(repo))]


__all__ = ["TaskAtomizerAgent", "MAX_ATOMIZATION_DEPTH"]
