"""Project-Initializer Agent (T044).

Bootstraps a per-project Spec Kit scaffold under `projects/<PROJ-ID>/`.
The mechanical part — copying upstream `.specify/{scripts,templates}/`
into the project's own `.specify/` — is delegated to
`speckit.runner.init_speckit_in`. The LLM portion renders the
project-level constitution from
`agents/templates/research_project_constitution.md` with token
substitution per FIX U3.

Stage transitions: `flesh_out_complete` → `project_initialized`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt, substitute
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.speckit.runner import init_speckit_in
from llmxive.types import AgentRegistryEntry, Project, Stage


CONSTITUTION_TEMPLATE_PATH = "agents/templates/research_project_constitution.md"


class ProjectInitializerAgent(Agent):
    def __init__(self, registry_entry: AgentRegistryEntry) -> None:
        super().__init__(registry_entry)

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = Path(__file__).resolve().parent.parent.parent.parent

        # Render the constitution template with project-specific tokens
        # BEFORE the LLM sees it (so the model adapts a concrete
        # constitution to the project's domain rather than fabricating
        # a substitution).
        title = ctx.metadata.get("title", ctx.project_id)
        field = ctx.metadata.get("field", "general")
        principal = ctx.metadata.get("principal_agent_name", "flesh_out")
        date = datetime.now(timezone.utc).date().isoformat()
        rendered_template = render_prompt(
            CONSTITUTION_TEMPLATE_PATH,
            {
                "project_id": ctx.project_id,
                "title": title,
                "field": field,
                "principal_agent_name": principal,
                "date": date,
            },
            repo_root=repo,
        )

        idea_summary = ""
        if ctx.inputs:
            idea_path = repo / ctx.inputs[0]
            if idea_path.exists():
                idea_summary = idea_path.read_text(encoding="utf-8")

        system_prompt = render_prompt(
            self.entry.prompt_path,
            {
                "project_id": ctx.project_id,
                "title": title,
                "field": field,
                "principal_agent_name": principal,
                "date": date,
            },
            repo_root=repo,
        )
        user_content = (
            f"# Rendered constitution template (with tokens substituted)\n\n"
            f"{rendered_template}\n\n"
            f"# Idea summary (for context)\n\n{idea_summary}\n\n"
            f"# Task\n\nReturn the final project constitution Markdown."
        )
        return [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_content),
        ]

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        project_dir = repo / "projects" / ctx.project_id

        # Mechanical step: scaffold .specify/ inside the project.
        init_speckit_in(project_dir)

        # Write the LLM-rendered constitution.
        constitution_path = project_dir / ".specify" / "memory" / "constitution.md"
        constitution_path.parent.mkdir(parents=True, exist_ok=True)
        constitution_text = response.text.strip()
        if not constitution_text.startswith("#"):
            # Defensive: ensure at least one h1 — pre-render the template
            # if the LLM returned something malformed.
            constitution_text = substitute(
                (Path(repo / CONSTITUTION_TEMPLATE_PATH).read_text(encoding="utf-8")),
                ctx.metadata,
            )
        constitution_path.write_text(constitution_text + "\n", encoding="utf-8")

        return [str(constitution_path.relative_to(repo))]


def transition_to_project_initialized(project: Project) -> Project:
    """Helper used by the pipeline graph to update project state."""
    if project.current_stage != Stage.FLESH_OUT_COMPLETE:
        raise ValueError(
            f"cannot initialize: project is at {project.current_stage.value}"
        )
    return project.model_copy(update={"current_stage": Stage.PROJECT_INITIALIZED})


__all__ = ["ProjectInitializerAgent", "transition_to_project_initialized"]
