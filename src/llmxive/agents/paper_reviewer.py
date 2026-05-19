"""Paper-Reviewer Agent (T097).

Reads the paper (LaTeX source + figure inventory + bibliography
verification status + proofreader flags) and emits a structured
review record under
`projects/<PROJ-ID>/paper/reviews/<reviewer-name>__<YYYY-MM-DD>__paper.md`.

Stage transitions are decided by the Advancement-Evaluator from the
accumulated review records.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.backends.router import chat_with_fallback
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


def _gather_raw_concat(source_dir: Path) -> str:
    """Return the full `.tex` corpus concatenated with no budget cap.
    Same file ordering as `_concat_tex` (entry-point file containing
    `\\documentclass` first). Callers that need a bounded corpus should
    pipe this through `_chunk_and_summarize` instead of `_concat_tex`."""
    if not source_dir.is_dir():
        return ""
    all_tex = sorted(source_dir.rglob("*.tex"))
    if not all_tex:
        return ""
    primary: Path | None = None
    for tex in all_tex:
        try:
            head = tex.read_text(encoding="utf-8", errors="ignore")[:4000]
        except OSError:
            continue
        if "\\documentclass" in head:
            primary = tex
            break
    ordering = ([primary] + [t for t in all_tex if t != primary]
                if primary else list(all_tex))
    blocks: list[str] = []
    for tex in ordering:
        rel = tex.relative_to(source_dir).as_posix()
        body = tex.read_text(encoding="utf-8", errors="ignore")
        blocks.append(f"=== {rel} ===\n{body}\n")
    return "\n".join(blocks)


def _chunk_corpus(text: str, *, max_chunk_size: int) -> list[str]:
    """Split `text` into chunks of at most `max_chunk_size` chars at
    natural LaTeX boundaries. Preference order:
      1. `\\section{` / `\\subsection{` / `\\subsubsection{` start
      2. `=== <path> ===` file-separator the gather pass emits
      3. blank-line paragraph break
      4. hard-cut at the budget (last resort).

    Each chunk is a self-contained slice — a downstream summarizer
    can summarize it without needing context from neighbours.
    """
    if len(text) <= max_chunk_size:
        return [text]
    # Collect boundary offsets in priority order. Strong-preference
    # boundaries are sections; weaker are file-separators; weakest is
    # paragraph breaks.
    strong = sorted({
        m.start()
        for m in re.finditer(r"\n\\(?:sub){0,2}section\b", text)
    } | {m.start() for m in re.finditer(r"\n=== [^\n]+ ===\n", text)})
    paras = sorted({m.start() for m in re.finditer(r"\n\n", text)})

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        if n - start <= max_chunk_size:
            chunks.append(text[start:])
            break
        budget_end = start + max_chunk_size
        cut: int | None = None
        # Prefer the latest strong boundary in [start+1, budget_end].
        strong_cands = [b for b in strong if start < b <= budget_end]
        if strong_cands:
            cut = max(strong_cands)
        else:
            para_cands = [b for b in paras if start < b <= budget_end]
            if para_cands:
                cut = max(para_cands)
        if cut is None or cut <= start:
            cut = budget_end
        chunks.append(text[start:cut])
        start = cut
    return chunks


_CHUNK_SUMMARY_PROMPT_PREFIX = """\
You are summarizing one chunk of a LaTeX paper for a downstream peer \
reviewer who cannot see the full source. The output MUST be SHORTER \
than the input (it's a summary, not a transcription). A good target is \
20-40% of the input length: long enough to preserve the technical \
content, short enough to fit alongside other chunk summaries in the \
reviewer's context budget.

Output plain LaTeX. Preserve LOSSLESSLY:

  - every \\section / \\subsection / \\subsubsection heading (verbatim)
  - every numeric claim, statistic, and percentage
  - every \\ref{...}, \\label{...}, \\cite{...}, \\citep{...}, \\citet{...}
  - every \\includegraphics / \\caption text (verbatim)
  - the structure of any tabular environment (column headers + a \
representative row); replace bulk content with `(... N rows omitted ...)`
  - any directly-quoted phrase that uses `\\emph` or scare quotes

Drop only redundant prose, verbose framing, and repetitive examples. Do \
NOT invent content. Do NOT add a preamble about what you're about to \
summarize — just emit the summary. Do NOT wrap the output in \
`\\begin{document}...\\end{document}` (it's already a fragment).

=== CHUNK ===
"""

_CHUNK_SUMMARY_PROMPT_SUFFIX = (
    "\n=== END CHUNK ===\n\n"
    "Remember: output must be SHORTER than input. Emit the summary now."
)


def _summarize_chunk(
    chunk: str,
    *,
    default_backend: str,
    fallback_backends: list[str],
    model: str,
) -> str:
    """Single real LLM call (no mocks) that summarizes one chunk of the
    paper's LaTeX source. Returns the model's summary. We assemble the
    prompt via string concatenation (not `.format`) so the chunk's own
    `\\section{...}` braces don't get interpreted as format placeholders.

    If the model violates the "shorter than input" contract (rare with
    the current prompt, but observed with tiny inputs), we hard-truncate
    to 60% of the input length so the chunked path doesn't inflate the
    final corpus beyond the budget."""
    prompt = _CHUNK_SUMMARY_PROMPT_PREFIX + chunk + _CHUNK_SUMMARY_PROMPT_SUFFIX
    response = chat_with_fallback(
        [ChatMessage(role="user", content=prompt)],
        default_backend=default_backend,
        fallback_backends=fallback_backends,
        model=model,
    )
    summary = (response.text or "").strip() or "(summarizer returned empty content)"
    # Defensive: if the model expanded instead of summarized, trim to
    # 60% of input. This preserves the head of the summary (where the
    # model tends to put structural content) and protects the final
    # corpus from inflating beyond `final_budget`.
    max_summary = int(len(chunk) * 0.6)
    if len(summary) > max_summary > 0:
        summary = summary[:max_summary].rstrip() + "\n%% (summary truncated to 60% of input)\n"
    return summary


def _cached_summarize(
    chunk: str,
    summarize_fn: Callable[[str], str],
    *,
    cache_dir: Path | None,
) -> str:
    """Memoize chunk summaries to disk so re-runs across reviewers
    (and across review rounds) don't re-pay the LLM cost for unchanged
    source. Key is sha256 of the chunk's bytes — any source-byte change
    invalidates the cache entry automatically."""
    if cache_dir is None:
        return summarize_fn(chunk)
    cache_dir.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256(chunk.encode("utf-8")).hexdigest()[:16]
    path = cache_dir / f"{h}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    summary = summarize_fn(chunk)
    path.write_text(summary, encoding="utf-8")
    return summary


def _build_corpus_with_summaries(
    source_dir: Path,
    *,
    final_budget: int = 180_000,
    chunk_size: int = 100_000,
    summarize_fn: Callable[[str], str] | None = None,
    cache_dir: Path | None = None,
) -> str:
    """Return a corpus for the reviewer prompt. If the raw `.tex`
    concatenation fits in `final_budget`, return verbatim. Otherwise:
    chunk the corpus, summarize each chunk with `summarize_fn`, and
    return a notice + joined summaries.

    The chunked path requires `summarize_fn`. Falling back to truncation
    when none is provided keeps unit tests (which run without a backend)
    working.
    """
    raw = _gather_raw_concat(source_dir)
    if not raw or len(raw) <= final_budget:
        return raw
    if summarize_fn is None:
        # No summarizer — fall back to truncation (legacy behavior).
        return _concat_tex(source_dir, max_chars=final_budget)
    chunks = _chunk_corpus(raw, max_chunk_size=chunk_size)
    summary_blocks: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        summary = _cached_summarize(chunk, summarize_fn, cache_dir=cache_dir)
        summary_blocks.append(
            f"=== AUTO-SUMMARIZED CHUNK {i}/{len(chunks)} "
            f"({len(chunk)} bytes -> {len(summary)} bytes) ===\n{summary}"
        )
    header = (
        "=== NOTICE: The full paper source exceeded the reviewer's "
        f"context budget ({len(raw)} > {final_budget} bytes). It was "
        f"split into {len(chunks)} chunks and each chunk was summarized "
        "by an LLM in isolation. The summaries preserve section "
        "headings, numeric claims, references, and quoted material; "
        "redundant prose was dropped. Treat the summaries as faithful "
        "but lossy transcripts of the original. ===\n\n"
    )
    return header + "\n\n".join(summary_blocks)


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

        # Chunked-summarization corpus: if the raw `.tex` fits in the
        # 180KB reviewer-prompt budget, use it verbatim; otherwise
        # delegate to per-chunk LLM summarization so the reviewer sees a
        # faithful (lossy) transcript of the whole paper instead of a
        # truncation marker. Summaries are cached on disk under
        # `paper/.chunk_summaries/` so the 12 specialist reviewers
        # (each calling this) share the cost across the project.
        def _summarize(chunk: str) -> str:
            return _summarize_chunk(
                chunk,
                default_backend=self.entry.default_backend.value,
                fallback_backends=[b.value for b in self.entry.fallback_backends],
                model=self.entry.default_model,
            )

        source_concat = _build_corpus_with_summaries(
            paper_dir / "source",
            summarize_fn=_summarize,
            cache_dir=paper_dir / ".chunk_summaries",
        )
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
        # Spec 012 / FR-014: per-specialist re-review protocol. When THIS
        # specialist (self.entry.name) has ≥1 prior paper-stage review
        # record for THIS project, prepend the shared rereview block
        # listing that specialist's MOST-RECENT prior action_items so the
        # model performs a diff-check rather than fresh critique.
        rereview_block = ""
        try:
            prior_for_self = reviews_store.prior_reviews_for_specialist(
                ctx.project_id, self.entry.name, stage="paper", repo_root=repo,
            )
        except Exception:  # noqa: BLE001 — defensive; prior-loading must not break review
            prior_for_self = []
        if prior_for_self:
            most_recent = prior_for_self[-1]
            prior_items_yaml = yaml.safe_dump(
                [{"id": ai.id, "text": ai.text, "severity": ai.severity}
                 for ai in most_recent.action_items],
                sort_keys=False,
            ) if most_recent.action_items else "[]\n"
            snippet_path = repo / "agents" / "prompts" / "_shared" / "rereview_block.md"
            try:
                snippet = snippet_path.read_text(encoding="utf-8")
            except OSError:
                snippet = ""
            if snippet:
                rereview_block = snippet.replace(
                    "{prior_action_items_yaml}", prior_items_yaml.strip()
                ) + "\n\n"

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
            f"{rereview_block}"
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
