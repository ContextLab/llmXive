"""Figure-Generation-Agent (T083).

Generates Python plotting code that reads from real data files in
`data/` and writes a figure to `paper/figures/`. The runtime then
runs the generated code in the code sandbox; if it produces the
expected output file, the task is complete.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _summarize_data_file(path: Path, *, max_chars: int = 400) -> str:
    if not path.exists():
        return "(file does not exist)"
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return "(unreadable)"
    head = text[:max_chars]
    return f"first {max_chars} chars:\n{head}"


class PaperFigureGenerationAgent(Agent):
    """Handles [kind:figure] tasks routed by the Paper-Implementer dispatcher."""

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        project_dir = repo / "projects" / ctx.project_id
        paper_dir = project_dir / "paper"

        figure_id = ctx.metadata.get("figure_id", "")
        target_path_rel = ctx.metadata.get("target_path", "")
        data_source_rel = ctx.metadata.get("data_source_path", "")
        data_source_path = repo / data_source_rel if data_source_rel else None
        caption = ctx.metadata.get("caption", "")

        constitution = paper_dir / ".specify" / "memory" / "constitution.md"
        paper_constitution = _read_optional(constitution)
        paper_plans = sorted((paper_dir / "specs").glob("*/plan.md"))
        paper_plan_text = paper_plans[0].read_text(encoding="utf-8") if paper_plans else ""

        data_summary = (
            _summarize_data_file(data_source_path) if data_source_path else "(no data path)"
        )

        system = render_prompt(
            "agents/prompts/paper_figure_generation.md",
            {
                "project_id": ctx.project_id,
                "figure_id": figure_id,
                "target_path": target_path_rel,
                "data_source_path": data_source_rel,
                "caption": caption,
            },
            repo_root=repo,
        )
        user = (
            f"# task_id\n{ctx.task_id}\n\n"
            f"# data_summary\n{data_summary}\n\n"
            f"# Paper constitution (figure-style guidance)\n\n{paper_constitution}\n\n"
            f"# Paper plan.md (toolkit + style)\n\n{paper_plan_text}\n\n"
            "# Task\n\nReturn the YAML document per the contract."
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
            raise RuntimeError(f"Figure-Generation-Agent returned invalid YAML: {exc}") from exc
        if not isinstance(doc, dict) or doc.get("verdict") != "completed":
            return []

        artifact = doc.get("artifact") or {}
        relpath = artifact.get("path")
        generator_relpath = artifact.get("generator_path")
        generator_contents = artifact.get("generator_contents", "")
        written: list[str] = []

        if generator_relpath and generator_contents:
            target = repo / generator_relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(generator_contents, encoding="utf-8")
            written.append(generator_relpath)

        # Run the generator in the sandbox to actually produce the figure.
        # Lazy import to avoid pulling httpx etc. at module load time.
        import sys

        if str(repo) not in sys.path:
            sys.path.insert(0, str(repo))
        try:
            from agents.tools.code_sandbox import run_python
        except ImportError:
            return written

        if generator_contents and relpath:
            project_dir = repo / "projects" / ctx.project_id
            paper_dir = project_dir / "paper"
            requirements = paper_dir / "requirements.txt"
            req_path = requirements if requirements.exists() else None
            result = run_python(
                generator_contents,
                working_dir=paper_dir,
                requirements_path=req_path,
                capture_output_dir=paper_dir / "figures",
            )
            if result.returncode == 0 and not result.timed_out:
                fig_path = repo / relpath
                if fig_path.exists():
                    written.append(relpath)

        return written


__all__ = ["PaperFigureGenerationAgent"]
