"""Proofreader-Agent (T087).

Reads the assembled paper LaTeX source and emits a flag list. An
empty flag list is a precondition for `paper_complete` (per FR-007's
proofreader-flag-list-empty rule).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _concat_paper_source(paper_source_dir: Path) -> str:
    if not paper_source_dir.is_dir():
        return ""
    out: list[str] = []
    for tex in sorted(paper_source_dir.rglob("*.tex")):
        rel = tex.relative_to(paper_source_dir).as_posix()
        body = tex.read_text(encoding="utf-8", errors="ignore")
        out.append(f"=== {rel} ===\n{body}\n")
    return "\n".join(out)


class ProofreaderAgent(Agent):
    """Handles [kind:proofread] tasks. Also runs as a precondition gate."""

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        project_dir = repo / "projects" / ctx.project_id
        paper_dir = project_dir / "paper"
        source_dir = paper_dir / "source"

        body = _concat_paper_source(source_dir)
        constitution = paper_dir / ".specify" / "memory" / "constitution.md"
        paper_constitution = _read_optional(constitution)

        system = render_prompt(
            "agents/prompts/proofreader.md",
            {"project_id": ctx.project_id},
            repo_root=repo,
        )
        user = (
            f"# Paper source\n\n{body}\n\n"
            f"# Paper constitution\n\n{paper_constitution}\n\n"
            "# Task\n\nReturn the YAML flag list per the contract."
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
            raise RuntimeError(f"Proofreader-Agent returned invalid YAML: {exc}") from exc
        if not isinstance(doc, dict):
            raise RuntimeError("Proofreader YAML must be a mapping")

        # Persist the flag list under the project's paper memory so the
        # paper_complete gate can read it.
        flags_path = (
            repo
            / "projects"
            / ctx.project_id
            / "paper"
            / ".specify"
            / "memory"
            / "proofreader_flags.yaml"
        )
        flags_path.parent.mkdir(parents=True, exist_ok=True)
        flags_path.write_text(yaml.safe_dump(doc, sort_keys=True), encoding="utf-8")
        return [str(flags_path.relative_to(repo))]


def proofreader_clean(project_id: str, *, repo_root: Path | None = None) -> bool:
    """Return True iff the most recent proofreader run had an empty flag list."""
    repo = repo_root or Path(__file__).resolve().parent.parent.parent.parent
    flags_path = (
        repo
        / "projects"
        / project_id
        / "paper"
        / ".specify"
        / "memory"
        / "proofreader_flags.yaml"
    )
    if not flags_path.exists():
        return False
    try:
        doc = yaml.safe_load(flags_path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return False
    if not isinstance(doc, dict):
        return False
    flags = doc.get("flags") or []
    return doc.get("verdict") == "clean" and not flags


__all__ = ["ProofreaderAgent", "proofreader_clean"]
