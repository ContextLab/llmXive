"""LaTeX-Build Agent (T090) + LaTeX-Fix Agent (T090).

The Build agent is mostly a wrapper around `pdflatex`; the LLM is
consulted only to summarize errors. The Fix agent is LLM-driven —
it edits .tex files to repair compile failures. The runtime alternates
build/fix until the build succeeds OR a consecutive-failure cap is
reached, at which point the project transitions to
`human_input_needed`.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import yaml

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _run_pdflatex(source_dir: Path, main_tex: str, output_dir: Path) -> tuple[int, str, str]:
    """Run `pdflatex -interaction=nonstopmode` twice. Returns (rc, stdout, stderr)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if shutil.which("pdflatex") is None:
        return 127, "", "pdflatex not on PATH"
    cmd = [
        "pdflatex",
        "-interaction=nonstopmode",
        "-file-line-error",
        f"-output-directory={output_dir}",
        main_tex,
    ]
    last_rc = 0
    last_out = ""
    last_err = ""
    for _ in range(2):
        proc = subprocess.run(
            cmd,
            cwd=str(source_dir),
            capture_output=True,
            text=True,
            timeout=300,
        )
        last_rc = proc.returncode
        last_out = proc.stdout or ""
        last_err = proc.stderr or ""
    return last_rc, last_out, last_err


class LatexBuildAgent(Agent):
    """Compiles LaTeX → PDF. Mostly mechanical; LLM only summarizes errors."""

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        # Mode B prompt — invoked only when the build fails.
        repo = Path(__file__).resolve().parent.parent.parent.parent
        error_log = ctx.metadata.get("error_log", "")
        system = render_prompt(
            "agents/prompts/latex_build.md",
            {"project_id": ctx.project_id, "mode": "B"},
            repo_root=repo,
        )
        user = (
            "Mode: B (summarize compilation errors)\n\n"
            f"# Error log\n\n{error_log[:8000]}\n\n"
            "Return the YAML failure summary per the contract."
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
            raise RuntimeError(f"LaTeX-Build returned invalid YAML: {exc}") from exc
        # Persist the failure summary so LaTeX-Fix can read it.
        if isinstance(doc, dict) and doc.get("verdict") == "failed":
            project_dir = repo / "projects" / ctx.project_id
            summary_path = (
                project_dir / "paper" / ".specify" / "memory" / "latex_build_failure.yaml"
            )
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(
                yaml.safe_dump(doc, sort_keys=True), encoding="utf-8"
            )
            return [str(summary_path.relative_to(repo))]
        return []


def build_paper(
    project_id: str,
    *,
    main_tex: str = "main.tex",
    repo_root: Path | None = None,
) -> dict[str, object]:
    """Mechanical build entry point. Returns a result dict with stdout/stderr."""
    repo = repo_root or Path(__file__).resolve().parent.parent.parent.parent
    paper_dir = repo / "projects" / project_id / "paper"
    source_dir = paper_dir / "source"
    pdf_dir = paper_dir / "pdf"

    if not (source_dir / main_tex).exists():
        return {
            "ok": False,
            "rc": 0,
            "stdout": "",
            "stderr": f"main_tex {main_tex} not found in {source_dir}",
            "pdf_path": None,
        }

    rc, out, err = _run_pdflatex(source_dir, main_tex, pdf_dir)
    pdf_name = main_tex.rsplit(".", 1)[0] + ".pdf"
    produced = pdf_dir / pdf_name
    return {
        "ok": rc == 0 and produced.exists(),
        "rc": rc,
        "stdout": out,
        "stderr": err,
        "pdf_path": str(produced) if produced.exists() else None,
    }


class LatexFixAgent(Agent):
    """Repairs LaTeX compile failures by editing .tex sources."""

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        project_dir = repo / "projects" / ctx.project_id
        paper_dir = project_dir / "paper"
        summary_path = paper_dir / ".specify" / "memory" / "latex_build_failure.yaml"
        error_summary = _read_optional(summary_path)

        # Concatenate every .tex source so the LLM can see what to edit.
        source_dir = paper_dir / "source"
        sources_block = ""
        if source_dir.is_dir():
            for tex in sorted(source_dir.rglob("*.tex")):
                rel = tex.relative_to(repo).as_posix()
                sources_block += f"\n=== {rel} ===\n{tex.read_text(encoding='utf-8')}\n"

        attempts = ctx.metadata.get("attempts_so_far", "0")

        system = render_prompt(
            "agents/prompts/latex_fix.md",
            {"project_id": ctx.project_id},
            repo_root=repo,
        )
        user = (
            f"# Error summary\n\n{error_summary}\n\n"
            f"# Source files\n\n{sources_block}\n\n"
            f"# Attempts so far\n{attempts}\n\n"
            "Return the YAML patch document per the contract."
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
            raise RuntimeError(f"LaTeX-Fix returned invalid YAML: {exc}") from exc
        if not isinstance(doc, dict) or doc.get("verdict") != "patched":
            return []
        written: list[str] = []
        for patch in doc.get("patches", []) or []:
            relpath = patch.get("path")
            contents = patch.get("contents", "")
            if not relpath:
                continue
            target = repo / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(contents, encoding="utf-8")
            written.append(relpath)
        return written


__all__ = ["LatexBuildAgent", "LatexFixAgent", "build_paper"]
