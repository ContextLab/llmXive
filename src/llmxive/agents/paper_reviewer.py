"""Paper-Reviewer Agent (T097).

Reads the paper (LaTeX source + figure inventory + bibliography
verification status + proofreader flags) and emits a structured
review record under
`projects/<PROJ-ID>/paper/reviews/<reviewer-name>__<YYYY-MM-DD>__paper.md`.

Stage transitions are decided by the Advancement-Evaluator from the
accumulated review records.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.state import citations as citations_store
from llmxive.state import reviews as reviews_store
from llmxive.types import (
    AgentRegistryEntry,
    ReviewerKind,
    ReviewRecord,
)


_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(?P<frontmatter>.*?)\n---\s*\n(?P<body>.*)$",
    re.DOTALL,
)


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _concat_tex(source_dir: Path, *, max_chars: int = 60000) -> str:
    if not source_dir.is_dir():
        return ""
    chunks: list[str] = []
    total = 0
    for tex in sorted(source_dir.rglob("*.tex")):
        rel = tex.relative_to(source_dir).as_posix()
        body = tex.read_text(encoding="utf-8", errors="ignore")
        chunk = f"=== {rel} ===\n{body}\n"
        if total + len(chunk) > max_chars:
            chunks.append(f"=== (truncated; remaining files: {len(list(source_dir.rglob('*.tex'))) - len(chunks)}) ===\n")
            break
        chunks.append(chunk)
        total += len(chunk)
    return "\n".join(chunks)


def _summarize_figures(fig_dir: Path) -> str:
    if not fig_dir.is_dir():
        return "(no figures directory)"
    lines: list[str] = []
    for path in sorted(fig_dir.iterdir()):
        if path.is_file():
            lines.append(f"- `{path.name}` ({path.stat().st_size} bytes)")
    return "\n".join(lines) if lines else "(empty)"


def _summarize_pdf(pdf_dir: Path) -> str:
    if not pdf_dir.is_dir():
        return "(no pdf directory)"
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        return "(no PDF compiled yet)"
    out: list[str] = []
    for pdf in pdfs:
        size = pdf.stat().st_size
        out.append(f"- `{pdf.name}` ({size} bytes)")
    return "\n".join(out)


class PaperReviewerAgent(Agent):
    """Casts a single paper-quality vote on a project's compiled paper."""

    def __init__(self, registry_entry: AgentRegistryEntry) -> None:
        super().__init__(registry_entry)

    def _project_dir(self, ctx: AgentContext) -> Path:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        return repo / "projects" / ctx.project_id

    def _paper_feature_dir(self, project_dir: Path) -> Path | None:
        # Prefer the dir that actually has tasks.md, then spec.md.
        candidates = sorted((project_dir / "paper").glob("specs/*/"))
        if not candidates:
            return None
        for c in candidates:
            if (c / "tasks.md").exists():
                return c
        for c in candidates:
            if (c / "spec.md").exists():
                return c
        return candidates[0]

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        project_dir = self._project_dir(ctx)
        paper_dir = project_dir / "paper"
        feature_dir = self._paper_feature_dir(project_dir)
        # No hard-fail when feature_dir is missing: arXiv-intake papers
        # (e.g., PROJ-564, PROJ-566 — papers ingested verbatim from
        # arXiv with `paper/metadata.json` + `paper/source/`) never ran
        # through the home-grown spec→plan→tasks→implement pipeline, so
        # `paper/specs/<n>-<slug>/` simply doesn't exist. The reviewer
        # can still read the PDF + source + figures + bibliography.
        # handle_response() falls back to hashing `paper/metadata.json`
        # for the artifact_hash / artifact_path fields when feature_dir
        # is None.
        is_arxiv_intake = feature_dir is None and (paper_dir / "metadata.json").is_file()
        if feature_dir is None and not is_arxiv_intake:
            raise FileNotFoundError(
                f"no paper specs/ feature dir and no paper/metadata.json "
                f"in {project_dir} — paper review cannot proceed without "
                "either a generated spec or an intake-metadata artifact"
            )

        source_concat = _concat_tex(paper_dir / "source")
        figures_summary = _summarize_figures(paper_dir / "figures")
        pdf_summary = _summarize_pdf(paper_dir / "pdf")
        proofreader_flags = _read_optional(
            paper_dir / ".specify" / "memory" / "proofreader_flags.yaml"
        )

        # Bibliography summary from state/citations.
        cits = citations_store.load(ctx.project_id, repo_root=repo)
        if cits:
            bib_lines = [
                f"- {c.cite_id} ({c.kind.value}): {c.value} — {c.verification_status.value}"
                for c in cits
            ]
            bib_summary = "\n".join(bib_lines)
        else:
            bib_summary = "(no citations recorded)"

        prior = reviews_store.list_for(ctx.project_id, stage="paper", repo_root=repo)
        prior_block = (
            "\n\n".join(
                f"- {r.reviewer_name} ({r.reviewer_kind.value}): {r.verdict} — {r.feedback[:120]}"
                for r in prior
            )
            or "(no prior paper reviews)"
        )

        # Use the registry entry's prompt_path so specialist reviewers
        # (paper_reviewer_writing_quality, _claim_accuracy, etc.) load
        # their own focused prompts. The generic paper_reviewer agent
        # falls back to agents/prompts/paper_reviewer.md.
        prompt_path = self.entry.prompt_path or "agents/prompts/paper_reviewer.md"
        system = render_prompt(
            prompt_path,
            {"project_id": ctx.project_id, "reviewer_name": self.entry.name},
            repo_root=repo,
        )
        user = (
            f"# project_id\n{ctx.project_id}\n\n"
            f"# title\n{ctx.metadata.get('title', '')}\n\n"
            f"# Paper LaTeX source\n\n{source_concat}\n\n"
            f"# Compiled PDFs\n\n{pdf_summary}\n\n"
            f"# Figures\n\n{figures_summary}\n\n"
            f"# Bibliography\n\n{bib_summary}\n\n"
            f"# Proofreader flags\n\n{proofreader_flags}\n\n"
            f"# Prior paper reviews\n\n{prior_block}\n\n"
            "# Task\n\nReturn the review record per the contract."
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        repo = Path(__file__).resolve().parent.parent.parent.parent
        text = response.text.strip()
        match = _FRONTMATTER_RE.match(text)
        if not match:
            raise RuntimeError("paper_reviewer: response missing YAML frontmatter")
        front = yaml.safe_load(match.group("frontmatter"))
        body = match.group("body").strip()
        if not isinstance(front, dict):
            raise RuntimeError("paper_reviewer: frontmatter must be a YAML mapping")

        # Force runtime-known fields.
        front["reviewer_name"] = self.entry.name
        front["reviewer_kind"] = ReviewerKind.LLM.value
        front["model_name"] = response.model
        front["backend"] = response.backend
        front["prompt_version"] = self.entry.prompt_version
        front["reviewed_at"] = datetime.now(timezone.utc).isoformat()

        # Compute artifact_hash + artifact_path. Two paths:
        #   (a) Home-grown paper pipeline: tasks.md under paper/specs/<n>-<slug>/
        #   (b) arXiv-intake paper: paper/metadata.json (no feature_dir)
        # In both cases artifact_path satisfies the schema regex
        # `^projects/PROJ-\d{3,}-[a-z0-9-]+/.+`.
        project_dir = self._project_dir(ctx)
        feature_dir = self._paper_feature_dir(project_dir)
        from llmxive.state.project import hash_file

        if feature_dir is not None:
            tasks_path = feature_dir / "tasks.md"
            if tasks_path.exists():
                front["artifact_hash"] = hash_file(tasks_path)
                front["artifact_path"] = str(tasks_path.relative_to(repo))
        else:
            # arXiv-intake fallback — metadata.json is the canonical
            # per-project artifact summary (arxiv_id, title, authors,
            # source_files list, etc.). Stable + always present for
            # arXiv-submitted papers.
            meta_path = project_dir / "paper" / "metadata.json"
            if meta_path.is_file():
                front["artifact_hash"] = hash_file(meta_path)
                front["artifact_path"] = str(meta_path.relative_to(repo))

        record = ReviewRecord.model_validate(front)
        path = reviews_store.write(
            record,
            body=body,
            stage="paper",
            review_type="paper",
            produced_by_agent=None,
            repo_root=repo,
        )
        return [str(path.relative_to(repo))]


__all__ = ["PaperReviewerAgent"]
