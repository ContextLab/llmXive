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


def _concat_tex(source_dir: Path, *, max_chars: int = 180_000) -> str:
    """Concatenate .tex files for the reviewer prompt.

    Ordering matters: arXiv tarballs commonly have a tiny `extra_pkgs.tex`
    that sorts alphabetically BEFORE the multi-hundred-KB `main.tex`. With
    a small budget that ordering meant the reviewer saw only package
    declarations — never the actual paper body. We now:
      1. Promote the entry-point file (`\\documentclass`) to the front,
         and if needed include it truncated to fit the budget.
      2. Then include other files until the budget is exhausted.

    The default budget (~180KB ≈ 45K tokens) leaves headroom in a 128K
    context window for the system prompt, figure list, bibliography,
    prior reviews, and the response.
    """
    if not source_dir.is_dir():
        return ""
    all_tex = sorted(source_dir.rglob("*.tex"))
    if not all_tex:
        return ""

    # Locate the entry-point file (contains \documentclass). Skim only
    # the head of each file to avoid loading every tex twice.
    primary: Path | None = None
    for tex in all_tex:
        try:
            head = tex.read_text(encoding="utf-8", errors="ignore")[:4000]
        except OSError:
            continue
        if "\\documentclass" in head:
            primary = tex
            break

    ordering = [primary] + [t for t in all_tex if t != primary] if primary else list(all_tex)

    chunks: list[str] = []
    total = 0
    included = 0
    for tex in ordering:
        rel = tex.relative_to(source_dir).as_posix()
        body = tex.read_text(encoding="utf-8", errors="ignore")
        chunk = f"=== {rel} ===\n{body}\n"
        if total + len(chunk) > max_chars:
            remaining_budget = max(max_chars - total - 200, 0)
            if remaining_budget > 0 and included == 0:
                # Always include at least the primary file, even if it
                # needs to be cut. A truncated entry-point is far more
                # useful than only seeing package declarations.
                chunks.append(chunk[:remaining_budget] +
                              f"\n=== ({rel} truncated to fit budget) ===\n")
                total += remaining_budget
                included += 1
            files_omitted = len(ordering) - included
            chunks.append(
                f"=== ({files_omitted} additional .tex file(s) omitted to fit budget) ===\n"
            )
            break
        chunks.append(chunk)
        total += len(chunk)
        included += 1
    return "\n".join(chunks)


def _summarize_bibfile(source_dir: Path, *, max_chars: int = 30_000) -> str:
    """For arXiv-intake papers, state/citations/<PROJ>.yaml is empty.
    Surface ref.bib (or any .bib) so the reviewer can see what's cited.
    """
    if not source_dir.is_dir():
        return ""
    bibs = sorted(source_dir.rglob("*.bib"))
    if not bibs:
        return ""
    parts: list[str] = []
    total = 0
    for bib in bibs:
        rel = bib.relative_to(source_dir).as_posix()
        body = bib.read_text(encoding="utf-8", errors="ignore")
        head = f"=== {rel} ===\n"
        if total + len(head) + len(body) > max_chars:
            remaining = max(max_chars - total - len(head) - 100, 0)
            if remaining > 0:
                parts.append(head + body[:remaining] + "\n=== (truncated) ===\n")
                total += len(head) + remaining
            break
        parts.append(head + body + "\n")
        total += len(head) + len(body)
    return "\n".join(parts)


def _summarize_figures(fig_dir: Path) -> str:
    if not fig_dir.is_dir():
        return "(no figures directory)"
    lines: list[str] = []
    for path in sorted(fig_dir.iterdir()):
        if path.is_file():
            lines.append(f"- `{path.name}` ({path.stat().st_size} bytes)")
    return "\n".join(lines) if lines else "(empty)"


def _collect_figures_from_arxiv_source(source_dir: Path) -> str:
    """For arXiv-intake papers, figures live inside the source tarball
    under conventional subdirs (figures/, figs/, pics/, images/, plots/,
    Figures/, etc.) — NOT under paper/figures/. Discover them by
    extension across `source/**` so the reviewer can comment on them.

    Returns a single-line-per-figure listing. Capped at 200 entries to
    keep the prompt bounded.
    """
    if not source_dir.is_dir():
        return "(no source directory)"
    fig_exts = {".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg", ".tikz", ".gif"}
    lines: list[str] = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in fig_exts:
            continue
        # Skip top-level paper PDFs (the compiled output goes to
        # paper/pdf/, but some arxiv tarballs include the source PDF too).
        rel = path.relative_to(source_dir).as_posix()
        if rel.endswith(".pdf") and "/" not in rel:
            continue
        lines.append(f"- `{rel}` ({path.stat().st_size} bytes)")
        if len(lines) >= 200:
            lines.append("- (truncated at 200 entries)")
            break
    return "\n".join(lines) if lines else "(no figure-like files found in source)"


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
        # For arxiv-intake papers, figures live inside source/ (not
        # paper/figures/). Fall back to scanning source/ when the
        # canonical figures dir is empty/missing so the reviewer can
        # actually see what visual artifacts exist.
        figures_summary = _summarize_figures(paper_dir / "figures")
        if is_arxiv_intake or figures_summary.startswith("("):
            arxiv_figs = _collect_figures_from_arxiv_source(paper_dir / "source")
            if not arxiv_figs.startswith("(no"):
                figures_summary = arxiv_figs
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
            # arXiv-intake fallback: state/citations is never populated for
            # papers ingested verbatim, so surface the raw .bib file(s)
            # from paper/source/ — the reviewer can at least see what's
            # being cited and judge whether the reference set is sensible.
            bib_fallback = _summarize_bibfile(paper_dir / "source")
            bib_summary = bib_fallback or "(no citations recorded)"

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
        # arXiv-intake metadata block — surface the upstream context the
        # LLM needs to review a third-party paper (vs. a home-grown one).
        intake_block = ""
        if is_arxiv_intake:
            import json as _json
            try:
                meta = _json.loads((paper_dir / "metadata.json").read_text(encoding="utf-8"))
            except (OSError, _json.JSONDecodeError):
                meta = {}
            authors = ", ".join(meta.get("authors", []) or []) or "(unknown)"
            arxiv_url = meta.get("arxiv_url") or (
                f"https://arxiv.org/abs/{meta['arxiv_id']}" if meta.get("arxiv_id") else "(unknown)"
            )
            intake_block = (
                "# Paper provenance — IMPORTANT context\n\n"
                "This is an arXiv-submitted paper ingested verbatim from the "
                "public archive. The llmXive pipeline did NOT generate it; you "
                "are reviewing a third-party manuscript. The paper's authors "
                "are listed below; the submitter field is the llmXive intake "
                "agent that filed it, not an author.\n\n"
                f"- arXiv URL: {arxiv_url}\n"
                f"- Paper authors: {authors}\n"
                f"- Title (as recorded by intake): {meta.get('title', '(none)')}\n"
                f"- Submitter (intake actor): {meta.get('submitter', '(unknown)')}\n\n"
                "Focus your review on the paper itself — claims, methodology, "
                "figures, evidence — not on the speckit/plan/tasks artifacts "
                "that don't exist for arXiv-ingested papers.\n\n"
            )
        user = (
            f"# project_id\n{ctx.project_id}\n\n"
            f"# title\n{ctx.metadata.get('title', '')}\n\n"
            f"{intake_block}"
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

        # Normalize score: the LLM occasionally picks a verdict but
        # forgets the verdict↔score binding (e.g., verdict=accept with
        # score=0.0 or score=1.0). The score is purely derived from the
        # verdict, so we recompute it deterministically. This avoids
        # losing a substantive review to a numeric-formatting slip.
        verdict = front.get("verdict")
        if verdict == "accept":
            front["score"] = 0.5
        elif verdict in {"reject", "minor_revision", "full_revision",
                         "major_revision_writing", "major_revision_science",
                         "fundamental_flaws"}:
            front["score"] = 0.0

        # Spec 012 FR-018/019: normalize action_items emitted by the LLM.
        # The prompt tells the LLM to leave `id` blank and let the system
        # derive it from text via the canonical action_item_id() helper.
        # We also tolerate the LLM accidentally including an `id` (use it
        # only if it matches the canonical hex pattern; else recompute).
        items = front.get("action_items") or []
        if not isinstance(items, list):
            items = []
        from llmxive.types import action_item_id  # local import to avoid cycle at module load
        import re as _re
        normalized: list[dict] = []
        for raw in items:
            if not isinstance(raw, dict):
                continue
            text = raw.get("text")
            severity = raw.get("severity")
            if not text or severity not in ("writing", "science", "fatal"):
                continue
            raw_id = raw.get("id") or ""
            if not _re.fullmatch(r"[0-9a-f]{12}", str(raw_id)):
                raw_id = action_item_id(text)
            normalized.append({"id": raw_id, "text": text, "severity": severity})
        front["action_items"] = normalized

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
