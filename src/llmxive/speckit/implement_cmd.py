"""Implementer Agent — drives /speckit.implement (T054).

Reads the project's tasks.md, picks the next incomplete `[ ] T###`,
and either (a) writes the artifact the task describes, (b) marks the
task escalated to `human_input_needed`, or (c) requests atomization
(handled in US9). Persists progress per-task by checking off the box
in tasks.md.

Stage transitions:
  `analyzed` → `in_progress` (first task picked) →
              `research_complete` (last `[ ]` becomes `[X]`).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.config import LEAF_TASK_BUDGET_SECONDS
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext


_TASK_RE = re.compile(
    r"^- \[(?P<status>[ Xx])\]\s+(?P<id>T\d+)\b(?P<rest>.*)$",
    re.MULTILINE,
)


class ImplementerAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.implement"

    def _feature_dir(self, ctx: SlashCommandContext) -> Path:
        candidates = sorted(ctx.project_dir.glob("specs/*/"))
        if not candidates:
            raise FileNotFoundError(f"no specs/ feature dir in {ctx.project_dir}")
        return candidates[0]

    def _next_incomplete(self, tasks_text: str) -> tuple[str, str] | None:
        for m in _TASK_RE.finditer(tasks_text):
            if m.group("status") == " ":
                return m.group("id"), m.group(0)
        return None

    def _all_complete(self, tasks_text: str) -> bool:
        return all(m.group("status") in {"X", "x"} for m in _TASK_RE.finditer(tasks_text))

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        feature_dir = self._feature_dir(ctx)
        tasks_path = feature_dir / "tasks.md"
        tasks_text = tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else ""
        next_task = self._next_incomplete(tasks_text)
        completed = [m.group("id") for m in _TASK_RE.finditer(tasks_text)
                     if m.group("status") in {"X", "x"}]
        return {
            "feature_dir": str(feature_dir),
            "tasks_path": str(tasks_path),
            "tasks_text": tasks_text,
            "next_task_id": next_task[0] if next_task else None,
            "next_task_line": next_task[1] if next_task else None,
            "completed_task_ids": completed,
            "all_complete": next_task is None and bool(completed),
        }

    def build_prompt(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
    ) -> list[ChatMessage]:
        repo = ctx.project_dir.parent.parent
        if mechanical_output.get("all_complete") or not mechanical_output.get("next_task_id"):
            # No-op prompt: the LLM is invoked but should return a no-op.
            return [
                ChatMessage(role="system", content="No incomplete tasks remain."),
                ChatMessage(role="user", content="Reply with `task_id: NONE\\nverdict: completed` only."),
            ]
        system = render_prompt(
            "agents/prompts/implementer.md",
            {
                "project_id": ctx.project_id,
                "next_task_id": mechanical_output["next_task_id"] or "",
            },
            repo_root=repo,
        )
        user = (
            f"# tasks.md\n\n{mechanical_output['tasks_text']}\n\n"
            f"# next task line\n\n{mechanical_output['next_task_line']}\n\n"
            f"# completed task ids\n{mechanical_output['completed_task_ids']}\n\n"
            f"# wall_clock_budget_seconds\n{LEAF_TASK_BUDGET_SECONDS}\n\n"
            "# Task\n\nReturn the YAML implementation report."
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def write_artifacts(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
        llm_response: ChatResponse,
    ) -> list[str]:
        repo = ctx.project_dir.parent.parent
        if mechanical_output.get("all_complete") or not mechanical_output.get("next_task_id"):
            return []

        try:
            doc = yaml.safe_load(llm_response.text)
        except yaml.YAMLError as exc:
            raise RuntimeError(f"Implementer returned invalid YAML: {exc}") from exc
        if not isinstance(doc, dict):
            raise RuntimeError("Implementer YAML must be a mapping")

        task_id = mechanical_output["next_task_id"]
        verdict = doc.get("verdict")
        written: list[str] = []

        if verdict == "completed":
            for art in doc.get("artifacts", []) or []:
                relpath = art.get("path")
                contents = art.get("contents", "")
                if not relpath:
                    continue
                target = repo / relpath
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(contents, encoding="utf-8")
                written.append(relpath)
            # Check off the task in tasks.md.
            tasks_path = Path(mechanical_output["tasks_path"])
            text = tasks_path.read_text(encoding="utf-8")
            text = re.sub(
                rf"^- \[ \] ({re.escape(task_id)}\b)",
                r"- [X] \1",
                text,
                count=1,
                flags=re.MULTILINE,
            )
            tasks_path.write_text(text, encoding="utf-8")
            written.append(str(tasks_path.relative_to(repo)))
        elif verdict == "failed":
            escalate_marker = (
                ctx.project_dir / ".specify" / "memory" / "human_input_needed.yaml"
            )
            escalate_marker.parent.mkdir(parents=True, exist_ok=True)
            escalate_marker.write_text(
                yaml.safe_dump(
                    {
                        "reason": doc.get("failure", {}).get("reason", "unspecified"),
                        "task_id": task_id,
                    }
                ),
                encoding="utf-8",
            )
        elif verdict == "atomize":
            # Recorded for the Task-Atomizer Agent (US9) to pick up.
            atomize_dir = ctx.project_dir / "code" / ".tasks"
            atomize_dir.mkdir(parents=True, exist_ok=True)
            (atomize_dir / f"{task_id}.atomize.yaml").write_text(
                yaml.safe_dump(doc.get("atomize", {})),
                encoding="utf-8",
            )

        return written


__all__ = ["ImplementerAgent"]
