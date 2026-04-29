"""Statistics-Agent (T085).

Performs a single inferential analysis per invocation: writes both
the analysis script and the LaTeX prose that quotes the script's
output. The runtime runs the script in the code sandbox and pipes the
JSON-printed values back into the prose template at integration time.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


class PaperStatisticsAgent(Agent):
    """Handles [kind:statistics] tasks routed by the Paper-Implementer dispatcher."""

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        project_dir = repo / "projects" / ctx.project_id
        paper_dir = project_dir / "paper"

        claim_id = ctx.metadata.get("claim_id", "")
        claim_text = ctx.metadata.get("claim_text", "")
        data_source_rel = ctx.metadata.get("data_source_path", "")
        analysis_kind = ctx.metadata.get("analysis_kind", "")

        constitution = paper_dir / ".specify" / "memory" / "constitution.md"
        paper_constitution = _read_optional(constitution)

        system = render_prompt(
            "agents/prompts/paper_statistics.md",
            {
                "project_id": ctx.project_id,
                "claim_id": claim_id,
                "data_source_path": data_source_rel,
            },
            repo_root=repo,
        )
        user = (
            f"# task_id\n{ctx.task_id}\n\n"
            f"# claim_id\n{claim_id}\n\n"
            f"# claim_text\n{claim_text}\n\n"
            f"# analysis_kind (optional)\n{analysis_kind}\n\n"
            f"# data_source_path\n{data_source_rel}\n\n"
            f"# Paper constitution (statistics discipline)\n\n{paper_constitution}\n\n"
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
            raise RuntimeError(f"Statistics-Agent returned invalid YAML: {exc}") from exc
        if not isinstance(doc, dict) or doc.get("verdict") != "completed":
            return []

        written: list[str] = []
        artifact = doc.get("artifact") or {}
        prose_relpath = artifact.get("path")
        prose_contents = artifact.get("contents", "")
        if prose_relpath and prose_contents:
            (repo / prose_relpath).parent.mkdir(parents=True, exist_ok=True)
            (repo / prose_relpath).write_text(prose_contents, encoding="utf-8")
            written.append(prose_relpath)

        analysis = doc.get("analysis_script") or {}
        script_relpath = analysis.get("path")
        script_contents = analysis.get("contents", "")
        if script_relpath and script_contents:
            (repo / script_relpath).parent.mkdir(parents=True, exist_ok=True)
            (repo / script_relpath).write_text(script_contents, encoding="utf-8")
            written.append(script_relpath)

            # Run the analysis script in the sandbox; persist the printed
            # JSON to a sibling `.result.json` so the integrator can pipe
            # values into the prose template.
            import sys

            if str(repo) not in sys.path:
                sys.path.insert(0, str(repo))
            try:
                from agents.tools.code_sandbox import run_python
            except ImportError:
                return written

            paper_dir = repo / "projects" / ctx.project_id / "paper"
            requirements = paper_dir / "requirements.txt"
            req_path = requirements if requirements.exists() else None
            result = run_python(
                script_contents,
                working_dir=paper_dir,
                requirements_path=req_path,
            )
            if result.returncode == 0 and not result.timed_out:
                last_line = ""
                for line in result.stdout.strip().splitlines():
                    last_line = line.strip()
                try:
                    payload = json.loads(last_line) if last_line else None
                except json.JSONDecodeError:
                    payload = None
                if payload is not None:
                    out = (repo / script_relpath).with_suffix(".result.json")
                    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                    written.append(str(out.relative_to(repo)))

        return written


__all__ = ["PaperStatisticsAgent"]
