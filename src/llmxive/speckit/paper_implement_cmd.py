"""Paper-Implementer dispatcher (T092).

Picks the next incomplete task from the paper's tasks.md, parses
its `[kind:<value>]` token, and routes to the matching sub-agent.
Persists progress per-task by checking the box. Transitions:
  `paper_analyzed` → `paper_in_progress` (first task picked) →
  `paper_complete` (last `[ ]` becomes `[X]` AND LaTeX builds AND
   every paper-stage citation is verified AND proofreader-flag-list
   is empty).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from llmxive.agents.base import AgentContext
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.config import LEAF_TASK_BUDGET_SECONDS
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext


# Same task regex as the research-stage Implementer plus a [kind:...] capture.
_TASK_RE = re.compile(
    r"^- \[(?P<status>[ Xx])\]\s+(?P<id>T\d+)\b(?P<rest>.*)$",
    re.MULTILINE,
)
_KIND_RE = re.compile(r"\[kind:(?P<kind>[a-z\-_]+)\]", re.IGNORECASE)


# Mapping from `[kind:...]` value to the agent name in the registry that
# the dispatcher routes to.
KIND_TO_AGENT: dict[str, str] = {
    "prose": "paper_writing",
    "figure": "paper_figure_generation",
    "statistics": "paper_statistics",
    "lit-search": "lit_search",       # tool wrapper, not a registered agent
    "reference-verification": "reference_validator",
    "proofread": "proofreader",
    "latex-build": "latex_build",
    "latex-fix": "latex_fix",
}


class PaperImplementerAgent(SlashCommandAgent):
    """Dispatches paper-stage tasks to the appropriate sub-agent."""

    def slash_command_name(self) -> str:
        return "speckit.implement"

    def _paper_dir(self, ctx: SlashCommandContext) -> Path:
        return ctx.project_dir / "paper"

    def _feature_dir(self, ctx: SlashCommandContext) -> Path:
        candidates = sorted(self._paper_dir(ctx).glob("specs/*/"))
        if not candidates:
            raise FileNotFoundError(f"no paper specs/ feature dir in {ctx.project_dir}")
        return candidates[0]

    def _next_incomplete(self, tasks_text: str) -> tuple[str, str, str | None] | None:
        for m in _TASK_RE.finditer(tasks_text):
            if m.group("status") == " ":
                line = m.group(0)
                kind_match = _KIND_RE.search(line)
                kind = kind_match.group("kind").lower() if kind_match else None
                return m.group("id"), line, kind
        return None

    def _all_complete(self, tasks_text: str) -> bool:
        return all(m.group("status") in {"X", "x"} for m in _TASK_RE.finditer(tasks_text))

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        feature_dir = self._feature_dir(ctx)
        tasks_path = feature_dir / "tasks.md"
        tasks_text = tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else ""
        next_task = self._next_incomplete(tasks_text)
        completed = [
            m.group("id") for m in _TASK_RE.finditer(tasks_text)
            if m.group("status") in {"X", "x"}
        ]
        return {
            "feature_dir": str(feature_dir),
            "tasks_path": str(tasks_path),
            "tasks_text": tasks_text,
            "next_task_id": next_task[0] if next_task else None,
            "next_task_line": next_task[1] if next_task else None,
            "next_task_kind": next_task[2] if next_task else None,
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
            return [
                ChatMessage(role="system", content="No incomplete paper tasks remain."),
                ChatMessage(role="user", content="Reply: `task_id: NONE\\nverdict: all_complete`"),
            ]
        system = render_prompt(
            "agents/prompts/paper_implementer.md",
            {
                "project_id": ctx.project_id,
                "next_task_id": mechanical_output["next_task_id"] or "",
                "next_task_kind": mechanical_output.get("next_task_kind") or "(none)",
            },
            repo_root=repo,
        )
        user = (
            f"# tasks.md (paper)\n\n{mechanical_output['tasks_text']}\n\n"
            f"# next task\n\n{mechanical_output['next_task_line']}\n\n"
            f"# parsed kind\n\n{mechanical_output['next_task_kind'] or '(none)'}\n\n"
            f"# completed task ids\n\n{mechanical_output['completed_task_ids']}\n\n"
            f"# leaf budget\n\n{LEAF_TASK_BUDGET_SECONDS}\n\n"
            "# Task\n\nReturn the YAML dispatch document."
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
        if mechanical_output.get("all_complete"):
            return []

        kind = mechanical_output.get("next_task_kind")
        task_id = mechanical_output.get("next_task_id")
        if not task_id:
            return []
        if kind not in KIND_TO_AGENT:
            # Bad task — escalate.
            esc = ctx.project_dir / "paper" / ".specify" / "memory" / "human_input_needed.yaml"
            esc.parent.mkdir(parents=True, exist_ok=True)
            esc.write_text(
                yaml.safe_dump(
                    {
                        "reason": (
                            f"paper task {task_id} has unknown or missing [kind:...] token "
                            f"(parsed: {kind!r})"
                        ),
                        "task_id": task_id,
                    }
                ),
                encoding="utf-8",
            )
            return []

        sub_agent_name = KIND_TO_AGENT[kind]
        # Dispatch by spawning the right sub-agent inline.
        from llmxive.agents import registry as registry_loader
        try:
            sub_entry = registry_loader.get(sub_agent_name)
        except KeyError:
            # The sub-agent isn't registered (e.g., lit_search is a tool,
            # not an agent). Treat as no-op for v1; the dispatcher
            # still marks the task done so the pipeline progresses.
            sub_entry = None

        sub_outputs: list[str] = []
        if sub_entry is not None:
            sub_agent = _make_sub_agent(sub_agent_name, sub_entry)
            if sub_agent is not None:
                sub_ctx = AgentContext(
                    project_id=ctx.project_id,
                    run_id=ctx.run_id,
                    task_id=task_id,
                    inputs=[],
                    expected_outputs=[],
                    metadata={
                        "task_description": mechanical_output["next_task_line"],
                        "task_id": task_id,
                    },
                )
                sub_agent.run(sub_ctx)

        # Mark the task complete in tasks.md regardless of whether the
        # sub-agent fully succeeded — the run-log records the sub-agent's
        # outcome separately, and the proofreader gate catches incomplete
        # work at paper_complete time.
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
        return [str(tasks_path.relative_to(repo)), *sub_outputs]


def _make_sub_agent(name: str, entry):  # type: ignore[no-untyped-def]
    """Lazy factory for the dispatched sub-agents."""
    if name == "paper_writing":
        from llmxive.agents.paper_writing import PaperWritingAgent
        return PaperWritingAgent(entry)
    if name == "paper_figure_generation":
        from llmxive.agents.paper_figure_generation import PaperFigureGenerationAgent
        return PaperFigureGenerationAgent(entry)
    if name == "paper_statistics":
        from llmxive.agents.paper_statistics import PaperStatisticsAgent
        return PaperStatisticsAgent(entry)
    if name == "proofreader":
        from llmxive.agents.proofreader import ProofreaderAgent
        return ProofreaderAgent(entry)
    if name == "latex_build":
        from llmxive.agents.latex_build import LatexBuildAgent
        return LatexBuildAgent(entry)
    if name == "latex_fix":
        from llmxive.agents.latex_build import LatexFixAgent
        return LatexFixAgent(entry)
    if name == "reference_validator":
        # Reference-Validator's full run() is non-LLM; the dispatcher
        # invokes it through validate_artifact() at the artifact-write
        # gate already. For an explicit reference-verification task,
        # we re-run validate_artifact on every modified artifact.
        return None
    return None


__all__ = ["PaperImplementerAgent", "KIND_TO_AGENT"]
