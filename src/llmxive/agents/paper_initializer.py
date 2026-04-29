"""Paper-Initializer Agent (T071).

Mirrors the research-stage Project-Initializer but operates against
`projects/<PROJ-ID>/paper/` and uses the paper-stage constitution
template at `agents/templates/paper_project_constitution.md`.

Stage transitions: `research_accepted` → `paper_drafting_init`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt, substitute
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.speckit.runner import init_speckit_in
from llmxive.types import AgentRegistryEntry, Project, Stage


PAPER_CONSTITUTION_TEMPLATE_PATH = "agents/templates/paper_project_constitution.md"


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


class PaperInitializerAgent(Agent):
    def __init__(self, registry_entry: AgentRegistryEntry) -> None:
        super().__init__(registry_entry)

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        title = ctx.metadata.get("title", ctx.project_id)
        field = ctx.metadata.get("field", "general")
        date = datetime.now(timezone.utc).date().isoformat()
        rendered_template = render_prompt(
            PAPER_CONSTITUTION_TEMPLATE_PATH,
            {
                "project_id": ctx.project_id,
                "title": title,
                "field": field,
                "date": date,
            },
            repo_root=repo,
        )

        # Pull research summary from the project's research-stage spec.
        project_dir = repo / "projects" / ctx.project_id
        research_spec = ""
        for spec_path in sorted(project_dir.glob("specs/*/spec.md")):
            research_spec = spec_path.read_text(encoding="utf-8")
            break

        system = render_prompt(
            self.entry.prompt_path,
            {
                "project_id": ctx.project_id,
                "title": title,
                "field": field,
                "date": date,
            },
            repo_root=repo,
        )
        user = (
            "# Rendered paper constitution template (with tokens substituted)\n\n"
            f"{rendered_template}\n\n"
            f"# Research-stage spec (for context)\n\n{research_spec[:8000]}\n\n"
            "# Task\n\nReturn the final paper constitution Markdown."
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        paper_dir = repo / "projects" / ctx.project_id / "paper"

        # Mechanical step: scaffold .specify/ inside the paper subdirectory.
        init_speckit_in(paper_dir)

        constitution_path = paper_dir / ".specify" / "memory" / "constitution.md"
        constitution_path.parent.mkdir(parents=True, exist_ok=True)
        text = response.text.strip()
        if not text.startswith("#"):
            text = substitute(
                (repo / PAPER_CONSTITUTION_TEMPLATE_PATH).read_text(encoding="utf-8"),
                ctx.metadata,
            )
        constitution_path.write_text(text + "\n", encoding="utf-8")
        return [str(constitution_path.relative_to(repo))]


def transition_to_paper_drafting_init(project: Project) -> Project:
    if project.current_stage != Stage.RESEARCH_ACCEPTED:
        raise ValueError(
            f"cannot initialize paper: project is at {project.current_stage.value}"
        )
    return project.model_copy(update={"current_stage": Stage.PAPER_DRAFTING_INIT})


__all__ = ["PaperInitializerAgent", "transition_to_paper_drafting_init"]
