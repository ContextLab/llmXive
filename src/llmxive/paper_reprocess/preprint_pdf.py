"""Reviewed-Preprint PDFs (2026-07-01 ethics change, design spec §4).

Two themed PDFs per preprint, written under ``paper/pdf/``:

- ``original-llmxive.pdf`` — a single ``llmxive.cls`` COVER page (title, authors,
  abstract, ingestion provenance, an llmXive blurb + link, and links to the peer
  review + the follow-up project) **prepended** to the UNTOUCHED original PDF via
  ``pypdf``. The original pages are copied byte-for-byte — never re-typeset — so a
  third party's work is presented exactly as they published it, with only an
  llmXive context page in front.
- ``peer-review-llmxive.pdf`` — the reviewer verdicts + feedback + consolidated
  action items laid out as a second ``llmxive.cls``-themed document.

Only the cover + review documents are compiled through LaTeX; the original body
is concatenated, guaranteeing the no-modification invariant mechanically.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from llmxive.config import repo_root as _repo_root
from llmxive.types import Project

_LLMXIVE_URL = "https://github.com/ContextLab/llmXive"
_CLS_REL = "papers/.style/llmxive.cls"


# --------------------------------------------------------------------------- #
# LaTeX escaping (deterministic, no network)
# --------------------------------------------------------------------------- #
def tex_escape(text: str, *, smart_quotes: bool = True) -> str:
    """Escape LaTeX special characters so metadata/prose renders literally.

    With ``smart_quotes`` (the default), straight ``"``/``'`` are turned into
    directional LaTeX quotes (````...''````) based on context, so an opening
    quote does not render as a closing one. Pass ``smart_quotes=False`` for code
    spans, where a literal quote is wanted.
    """
    if not text:
        return ""
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        # Unicode “smart” punctuation the LLMs emit -> LaTeX quotes/dashes.
        "“": "``", "”": "''",      # “ ”
        "‘": "`", "’": "'",         # ‘ ’
        "–": "--", "—": "---",      # en / em dash
        "…": r"\ldots{}",                 # …
    }
    _openers = " \t\n([{~/-"  # a straight quote after one of these opens
    out: list[str] = []
    prev = ""
    for ch in str(text):
        if smart_quotes and ch == '"':
            out.append("``" if (prev == "" or prev in _openers) else "''")
        elif smart_quotes and ch == "'":
            out.append("`" if (prev == "" or prev in _openers) else "'")
        else:
            out.append(replacements.get(ch, ch))
        prev = ch
    return "".join(out)


# --------------------------------------------------------------------------- #
# Original-PDF resolution
# --------------------------------------------------------------------------- #
def resolve_original_pdf(pdir: Path, metadata: dict, *, download: bool = True) -> Path | None:
    """Return the UNTOUCHED original paper PDF, or None if unresolvable.

    Preference order (never returns an ``*-llmxive.pdf`` — those are our
    modifications): a previously saved ``paper/pdf/original.pdf``; a source PDF
    matching the declared top-level tex stem; ``paper/source/main.pdf``; else, for
    an arXiv paper, download ``https://arxiv.org/pdf/<id>`` into
    ``paper/pdf/original.pdf`` and return it.
    """
    pdf_dir = pdir / "paper" / "pdf"
    saved = pdf_dir / "original.pdf"
    if saved.is_file():
        return saved

    source = pdir / "paper" / "source"
    stems = [Path(str(n)).stem for n in (metadata.get("toplevel_tex") or []) if str(n).strip()]
    candidates: list[Path] = [source / f"{s}.pdf" for s in stems]
    candidates.append(source / "main.pdf")
    for cand in candidates:
        # Guard: never treat a figure PDF or an llmXive-modified PDF as the body.
        if cand.is_file() and "-llmxive" not in cand.name:
            return cand

    if download:
        arxiv_id = str(metadata.get("arxiv_id") or "").strip()
        arxiv_url = str(metadata.get("arxiv_url") or "").strip()
        if not arxiv_id and "arxiv.org/abs/" in arxiv_url:
            arxiv_id = arxiv_url.rsplit("/", 1)[-1]
        if arxiv_id:
            pdf_dir.mkdir(parents=True, exist_ok=True)
            if _download_arxiv_pdf(arxiv_id, saved):
                return saved
    return None


def _download_arxiv_pdf(arxiv_id: str, out_path: Path) -> bool:
    """Download the canonical arXiv PDF. Returns True on a real PDF, else False."""
    import urllib.request

    url = f"https://arxiv.org/pdf/{arxiv_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "llmXive-preprint/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # urlopen targets a fixed arXiv host (not user input)
            data = resp.read()
    except Exception:  # offline / 404 → caller falls back to None
        return False
    if not data.startswith(b"%PDF"):
        return False
    out_path.write_bytes(data)
    return True


# --------------------------------------------------------------------------- #
# Cover page (llmxive.cls) + prepend
# --------------------------------------------------------------------------- #
def build_cover_tex(
    metadata: dict,
    ingestion_line: str,
    *,
    review_report_name: str | None = None,
    followup_project_id: str | None = None,
) -> str:
    """Return the LaTeX for a single ``llmxive.cls`` cover/info page."""
    title = tex_escape(str(metadata.get("title") or "Untitled preprint").strip())

    # Authors may be plain strings or ``{"name": ..., "kind": ...}`` records
    # (the intake stores the richer form). Render only the display name — never
    # the raw dict repr, which would dump ``{'name': 'X', 'kind': 'human'}`` onto
    # the cover byline.
    def _author_name(a: object) -> str:
        if isinstance(a, dict):
            return str(a.get("name") or a.get("author") or a.get("full_name") or "").strip()
        return str(a).strip()

    authors = [n for a in (metadata.get("authors") or []) if (n := _author_name(a))]
    author_line = tex_escape(", ".join(authors)) if authors else "Original authors"
    abstract = tex_escape(str(metadata.get("abstract") or "").strip())
    src_url = str(metadata.get("arxiv_url") or metadata.get("source_url") or "").strip()

    lines = [
        r"\documentclass{llmxive}",
        r"\usepackage{hyperref}",
        rf"\title{{{title}}}",
        rf"\author{{{author_line}}}",
        r"\paperstatus{Reviewed Preprint}",
        r"\begin{document}",
        r"\maketitle",
    ]
    if abstract:
        lines += [r"\begin{abstract}", abstract, r"\end{abstract}"]
    lines += [
        r"\section*{About this document}",
        (
            "This is a \\textbf{Reviewed Preprint}: a third-party paper that "
            "llmXive has \\emph{auto-reviewed} (with its LLM review panel) but "
            "\\emph{never modified}. The original manuscript follows this cover "
            "page \\textbf{exactly as published} by its authors --- llmXive "
            "re-typesets nothing and claims no authorship."
        ),
        "",
        rf"\noindent\textbf{{Provenance.}} {tex_escape(ingestion_line)}",
        "",
    ]
    if src_url:
        lines += [rf"\noindent\textbf{{Source.}} \url{{{src_url}}}", ""]
    lines += [
        r"\noindent\textbf{About llmXive.} llmXive is an automated platform for open "
        r"scientific discovery. Its specialist LLM agents advance their own ideas "
        r"from brainstorm to peer-reviewed paper, and they also review notable "
        r"third-party papers --- drawn from the most-downloaded papers on Hugging "
        r"Face and from submissions by human contributors. Every submitted paper is "
        r"reviewed by the LLM panel \emph{and} used to seed a new llmXive follow-up "
        r"study. This paper is one such third-party work: llmXive reviewed it but "
        rf"did not write it. Learn more at \url{{{_LLMXIVE_URL}}}.",
        "",
    ]
    if review_report_name:
        lines += [
            rf"\noindent\textbf{{Automated review.}} See the accompanying "
            rf"\texttt{{{tex_escape(review_report_name)}}} for the full reviewer report.",
            "",
        ]
    if followup_project_id:
        lines += [
            rf"\noindent\textbf{{llmXive follow-up.}} A separate llmXive study "
            rf"building on this work: \texttt{{{tex_escape(followup_project_id)}}}.",
            "",
        ]
    lines.append(r"\end{document}")
    return "\n".join(lines)


def render_llmxive_pdf(
    tex: str,
    work_dir: Path,
    *,
    repo_root: Path,
    basename: str,
    source_date_epoch: int = 0,
) -> Path:
    """Write ``tex`` + a copy of ``llmxive.cls`` into ``work_dir`` and compile it.

    ``source_date_epoch`` sets the ``\\today`` the cls footer prints (default 0 →
    1970-01-01); pass the ingestion epoch for a meaningful, still-deterministic
    cover date.
    """
    from llmxive.pipeline.pdf_pipeline.compile import compile_pdf

    work_dir.mkdir(parents=True, exist_ok=True)
    cls_src = repo_root / _CLS_REL
    if not cls_src.is_file():
        raise FileNotFoundError(f"llmxive.cls not found at {cls_src}")
    shutil.copy2(cls_src, work_dir / "llmxive.cls")
    tex_path = work_dir / f"{basename}.tex"
    tex_path.write_text(tex, encoding="utf-8")
    return compile_pdf(tex_path, out_dir=work_dir, source_date_epoch=source_date_epoch)


def _epoch_from_iso(iso: str) -> int:
    """Best-effort UTC epoch seconds from an ISO date/datetime; 0 on failure."""
    from datetime import datetime

    iso = (iso or "").strip()
    if not iso:
        return 0
    try:
        return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())
    except ValueError:
        try:
            return int(datetime.fromisoformat(iso[:10]).timestamp())
        except ValueError:
            return 0


def prepend_cover_to_pdf(cover_pdf: Path, original_pdf: Path, out_path: Path) -> Path:
    """Concatenate ``cover_pdf`` then ``original_pdf`` — original bytes untouched.

    Asserts the output page count is ``cover_pages + original_pages`` so a silent
    drop of the body can never pass. Returns ``out_path``.
    """
    from pypdf import PdfReader, PdfWriter

    cover = PdfReader(str(cover_pdf))
    original = PdfReader(str(original_pdf))
    writer = PdfWriter()
    for page in cover.pages:
        writer.add_page(page)
    for page in original.pages:
        writer.add_page(page)
    expected = len(cover.pages) + len(original.pages)
    if len(writer.pages) != expected:
        raise RuntimeError(
            f"prepend produced {len(writer.pages)} pages, expected {expected}"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as fh:
        writer.write(fh)
    return out_path


# --------------------------------------------------------------------------- #
# Markdown -> LaTeX (the review body is free-form markdown)
# --------------------------------------------------------------------------- #
import re as _re

# Inline tokens, in precedence order. Code first (so ** inside `code` is
# literal); then LaTeX math spans (``$...$``, ``$$...$$``, ``\(..\)``, ``\[..\]``)
# so their contents pass through VERBATIM and compile as math instead of being
# escaped into literal source; then markdown emphasis/links.
_MD_INLINE_RE = _re.compile(
    r"(?P<code>`[^`]+`)"
    r"|(?P<mathdd>\$\$[^$]+?\$\$)"
    r"|(?P<mathbrk>\\\[.+?\\\])"
    r"|(?P<mathpar>\\\(.+?\\\))"
    r"|(?P<math>\$[^$]+?\$)"
    r"|(?P<bold>\*\*(?:[^*]|\*(?!\*))+\*\*)"
    r"|(?P<bolddunderscore>__[^_]+__)"
    r"|(?P<italic>(?<![\*\w])\*(?!\s)[^*\n]+?\*(?!\*))"
    r"|(?P<link>\[[^\]]+\]\([^)\s]+\))"
)


def _md_inline(text: str, *, render_math: bool = True) -> str:
    """Convert inline markdown (bold/italic/code/links/math) to LaTeX, tex-escaping
    every literal run so the review prose renders as formatted text, not raw
    ``**...**`` / backtick source. LaTeX math spans pass through verbatim when
    ``render_math`` (the caller falls back to ``False`` if math breaks the
    compile, so the math shows as literal text rather than failing the report)."""
    out: list[str] = []
    pos = 0
    for m in _MD_INLINE_RE.finditer(text):
        out.append(tex_escape(text[pos:m.start()]))
        if m.group("code"):
            out.append(rf"\texttt{{{tex_escape(m.group('code')[1:-1], smart_quotes=False)}}}")
        elif m.group("mathdd") or m.group("mathbrk") or m.group("mathpar"):
            # Explicitly delimited math ($$..$$, \[..\], \(..\)) -> verbatim.
            frag = m.group(0)
            out.append(frag if render_math else tex_escape(frag))
        elif m.group("math"):
            # Single-$ inline math is ambiguous: reviewers sometimes quote a paper's
            # UNBALANCED $, which would pull a whole prose clause into math mode. If
            # the span reads like prose (a space-delimited 4+ letter word), keep it
            # literal; otherwise render it as math.
            frag = m.group(0)
            is_prose = bool(_re.search(r"\s[a-z]{4,}[\s,.;:]", frag[1:-1]))
            out.append(frag if (render_math and not is_prose) else tex_escape(frag))
        elif m.group("bold"):
            out.append(rf"\textbf{{{_md_inline(m.group('bold')[2:-2], render_math=render_math)}}}")
        elif m.group("bolddunderscore"):
            out.append(rf"\textbf{{{_md_inline(m.group('bolddunderscore')[2:-2], render_math=render_math)}}}")
        elif m.group("italic"):
            out.append(rf"\textit{{{_md_inline(m.group('italic')[1:-1], render_math=render_math)}}}")
        elif m.group("link"):
            lm = _re.match(r"\[([^\]]+)\]\(([^)\s]+)\)", m.group("link"))
            out.append(rf"{tex_escape(lm.group(1))} (\texttt{{{tex_escape(lm.group(2))}}})")
        pos = m.end()
    out.append(tex_escape(text[pos:]))
    return "".join(out)


def _markdown_to_latex(md: str, *, render_math: bool = True) -> str:
    """Convert a markdown block (headers, bullet/numbered lists, paragraphs,
    inline emphasis/code/math) into llmxive.cls-safe LaTeX. Deterministic, no deps."""
    out: list[str] = []
    para: list[str] = []
    list_open: str | None = None

    def flush_para() -> None:
        if para:
            out.append(_md_inline(" ".join(para).strip(), render_math=render_math))
            out.append("")
            para.clear()

    def close_list() -> None:
        nonlocal list_open
        if list_open:
            out.append(rf"\end{{{list_open}}}")
            list_open = None

    for raw in md.replace("\r\n", "\n").split("\n"):
        stripped = raw.strip()
        if not stripped:
            # A blank line ends a paragraph but does NOT close an open list: a
            # "loose" markdown list (blank lines between items) must stay a single
            # list so items number 1, 2, 3 rather than restarting at 1 each time.
            flush_para()
            continue
        hm = _re.match(r"^(#{1,6})\s+(.*)$", stripped)
        ul = _re.match(r"^[-*+]\s+(.*)$", stripped)
        ol = _re.match(r"^(\d+)[.)]\s+(.*)$", stripped)
        if hm:
            flush_para()
            close_list()
            out.append(rf"\subsection*{{{_md_inline(hm.group(2), render_math=render_math)}}}")
        elif ul or ol:
            flush_para()
            want = "itemize" if ul else "enumerate"
            if list_open != want:
                close_list()
                out.append(rf"\begin{{{want}}}")
                list_open = want
            body = ul.group(1) if ul else ol.group(2)
            out.append(rf"\item {_md_inline(body, render_math=render_math)}")
        else:
            close_list()
            para.append(stripped)
    flush_para()
    close_list()
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Peer-review report (llmxive.cls)
# --------------------------------------------------------------------------- #
def _prettify_reviewer(name: str) -> str:
    """``paper_reviewer_claim_accuracy`` -> ``Claim Accuracy`` for a clean header."""
    n = _lens_key(name)
    n = n.replace("_", " ").strip()
    return n.title() if n else str(name or "Reviewer")


def _lens_key(name: str) -> str:
    """Strip the ``paper_reviewer[_]`` prefix to the bare lens key."""
    return _re.sub(r"^(paper|research)_reviewer_?", "", str(name or "").strip())


# Pre-written, human-facing summary of what each specialist reviewer is directed
# to focus on (mirrors the mandate in agents/prompts/paper_reviewer_<lens>.md).
_REVIEWER_FOCUS: dict[str, str] = {
    "writing_quality": (
        "Reads the manuscript purely as prose --- clarity, flow, sentence-level "
        "grammar, paragraph cohesion, and overall readability --- setting the "
        "scientific content aside."
    ),
    "logical_consistency": (
        "Checks that each conclusion follows from its premises, flagging internal "
        "contradictions and causal claims that lack a stated supporting mechanism."
    ),
    "claim_accuracy": (
        "Verifies factual claims against their citations --- whether each cited "
        "source actually supports the claim attributed to it, and whether any "
        "claim is stated more strongly than its evidence permits."
    ),
    "overreach": (
        "Looks for over-claiming: conclusions extrapolated beyond what the data, "
        "methods, or scope justify, and whether the paper states its limitations "
        "honestly."
    ),
    "safety_ethics": (
        "Examines safety and ethics --- dual-use risk, IRB/IACUC and consent "
        "concerns, potential for harm, data privacy, and conflicts of interest "
        "--- aiming to be thorough but not alarmist."
    ),
    "scientific_evidence": (
        "Weighs the strength of the scientific evidence: sample sizes, controls, "
        "replication, effect sizes, p-hacking risk, and robustness of the central "
        "claims to plausible alternative explanations."
    ),
    "statistical_analysis": (
        "Scrutinizes the statistics --- appropriateness of tests, "
        "multiple-comparison handling, confidence intervals, model assumptions, "
        "and the reproducibility of the analyses."
    ),
    "jargon_police": (
        "Flags needless jargon: terms with plainer equivalents, acronyms not "
        "defined at first use, and passages that needlessly exclude "
        "non-specialist readers."
    ),
    "figure_critic": (
        "Inspects each figure directly --- the rendered image alongside its "
        "caption --- for clarity, axis labels and units, color choices, "
        "legibility at print scale, and whether the figure earns its place. This "
        "lens runs on a vision-capable model."
    ),
}


def _reviewer_focus(name: str) -> str:
    """The pre-written focus blurb for a reviewer, or a generic fallback."""
    key = _lens_key(name)
    return _REVIEWER_FOCUS.get(
        key,
        f"Focuses narrowly on the {key.replace('_', ' ')} aspect of the manuscript.",
    )


#: The public agent-prompt library (each reviewer's exact instructions live here).
_PROMPTS_DIR_URL = f"{_LLMXIVE_URL}/tree/main/agents/prompts"


def _prompt_url(reviewer_name: str) -> str:
    """GitHub URL of the prompt that defines a reviewer (``agents/prompts/<name>.md``)."""
    return f"{_LLMXIVE_URL}/blob/main/agents/prompts/{str(reviewer_name or '').strip()}.md"


def build_peer_review_tex(
    project: Project, records: list, *, action_items_md: str = "", render_math: bool = True
) -> str:
    """Render the reviewers' feedback + action items as an llmxive.cls doc.

    Deliberately shows NO per-reviewer accept/reject verdict: a Reviewed Preprint
    is advisory feedback only, so surfacing an internal verdict would contradict
    the report's own "nothing is accepted or rejected" statement. The review body
    is markdown and is converted to LaTeX so it renders formatted, not as source;
    ``$...$`` math renders as math when ``render_math`` (the builder retries with
    ``render_math=False`` if a stray/undefined macro breaks the compile).
    """
    title = tex_escape(f"llmXive Automated Review of {project.title}")
    ordered = sorted(records, key=lambda r: r.reviewer_name)
    lines = [
        r"\documentclass{llmxive}",
        r"\usepackage{amsmath,amssymb}",
        r"\usepackage{hyperref}",
        rf"\title{{{title}}}",
        r"\author{llmXive automated review panel}",
        r"\paperstatus{Automated Review}",
        r"\begin{document}",
        r"\maketitle",
    ]

    # --- prominent up-front disclaimer ------------------------------------- #
    lines += [
        (
            "\\noindent\\textbf{Please read first --- this review is fully "
            "automated and not checked by any human.} It is written by "
            "free, open-weight LLM agents that read the paper once, so "
            "\\textbf{errors, misreadings, and inaccuracies are likely}. Nothing "
            "here has been verified by a person. Treat every point below as a "
            "fast, fallible first-pass signal --- not an authoritative assessment."
        ),
        "",
    ]

    # --- opening: how the review was produced + who is on the panel --------- #
    lines += [
        r"\section*{How this review was produced}",
        (
            "This Reviewed Preprint was read by a panel of specialist llmXive LLM "
            "reviewers. Each reviewer is deliberately confined to a \\emph{single "
            "narrow lens} --- writing, logic, statistics, and so on --- and does "
            "not comment outside it, so that distinct concerns are surfaced "
            "independently rather than blurred into one overall score. The panel "
            "runs \\emph{once} over the paper. Every reviewer's exact instructions "
            "are public in the "
            rf"\href{{{_PROMPTS_DIR_URL}}}{{llmXive agent-prompt library}}; each "
            "section below also links the specific prompt it used."
        ),
        "",
        (
            "This report is \\textbf{advisory, automated feedback for the "
            "authors}. llmXive does not modify the paper, and \\textbf{nothing is "
            "accepted or rejected} on its basis --- every point below is a "
            "suggestion the authors are free to weigh. Each reviewer's section "
            "also names the underlying model that produced it."
        ),
        "",
    ]
    if ordered:
        # Panel makeup: just the roster (names) — each reviewer's full focus blurb
        # lives in its own section below, so it is NOT repeated here.
        names = [_prettify_reviewer(rec.reviewer_name) for rec in ordered]
        roster = (
            ", ".join(names[:-1]) + ", and " + names[-1] if len(names) > 1 else names[0]
        )
        lines.append(
            rf"\noindent\textbf{{This paper's panel ({len(names)} "
            rf"lens{'es' if len(names) != 1 else ''}):}} {tex_escape(roster)}. "
            r"Each lens is described in its own section below, alongside the model "
            r"and the exact prompt it used."
        )
        lines.append("")

    # --- one section per reviewer ------------------------------------------ #
    for rec in ordered:
        lines.append(rf"\section*{{{tex_escape(_prettify_reviewer(rec.reviewer_name))}}}")
        lines.append(rf"\noindent\textit{{{_md_inline(_reviewer_focus(rec.reviewer_name))}}}\\[4pt]")
        model = str(getattr(rec, "model_name", "") or "").strip() or "(model unrecorded)"
        lines.append(rf"\noindent\textbf{{Reviewer model:}} \texttt{{{tex_escape(model)}}}\\[2pt]")
        lines.append(
            rf"\noindent\textbf{{Prompt:}} \href{{{_prompt_url(rec.reviewer_name)}}}"
            rf"{{\texttt{{agents/prompts/{tex_escape(str(rec.reviewer_name))}.md}}}}\\[4pt]"
        )
        feedback = (getattr(rec, "feedback", "") or "").strip()
        if feedback:
            lines.append(_markdown_to_latex(feedback[:12000], render_math=render_math))
        items = getattr(rec, "action_items", None) or []
        if items:
            lines.append(r"\noindent\textbf{Action items.}")
            lines.append(r"\begin{itemize}")
            for item in items:
                sev = getattr(getattr(item, "severity", ""), "value", getattr(item, "severity", ""))
                lines.append(
                    rf"\item \textbf{{[{tex_escape(str(sev))}]}} "
                    rf"{_md_inline((item.text or '').strip(), render_math=render_math)}"
                )
            lines.append(r"\end{itemize}")
    lines.append(r"\end{document}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def build_preprint_pdfs(
    project: Project, *, repo_root: Path | None = None, download_original: bool = True
) -> dict[str, Path | None]:
    """Build both preprint PDFs under ``paper/pdf/``. Returns the written paths.

    ``original`` is ``None`` when no untouched original PDF could be resolved (the
    cover is still written as ``original-llmxive.pdf`` so the dashboard always has
    a themed artifact). ``peer_review`` is always built from the review records.
    """
    import json
    import tempfile

    from llmxive.paper_reprocess.preprint import ingestion_statement, load_preprint_manifest
    from llmxive.paper_reprocess.reprocess import project_dir
    from llmxive.state import reviews as reviews_store

    repo = repo_root or _repo_root()
    pdir = project_dir(project, repo)
    pdf_dir = pdir / "paper" / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    meta_path = pdir / "paper" / "metadata.json"
    metadata = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
    manifest = load_preprint_manifest(pdir) or {}
    ingestion_line = ingestion_statement(manifest) if manifest else "Ingested by llmXive."
    epoch = _epoch_from_iso(str(manifest.get("ingested_at") or ""))

    out: dict[str, Path | None] = {"original": None, "peer_review": None}
    review_name = "peer-review-llmxive.pdf"

    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        # --- cover + original --------------------------------------------- #
        cover_tex = build_cover_tex(
            metadata,
            ingestion_line,
            review_report_name=review_name,
            followup_project_id=manifest.get("followup_project_id"),
        )
        cover_pdf = render_llmxive_pdf(
            cover_tex, work / "cover", repo_root=repo, basename="cover",
            source_date_epoch=epoch,
        )
        original_target = pdf_dir / "original-llmxive.pdf"
        original_src = resolve_original_pdf(pdir, metadata, download=download_original)
        if original_src is not None:
            prepend_cover_to_pdf(cover_pdf, original_src, original_target)
        else:
            shutil.copy2(cover_pdf, original_target)  # cover-only fallback (no body found)
        out["original"] = original_target

        # --- peer-review report ------------------------------------------- #
        # Render the reviewers' ``$...$`` math as math; if a stray or
        # paper-defined (undefined-here) macro makes lualatex fail, retry once
        # with the math shown as literal text so a single bad expression never
        # costs the whole report.
        records = reviews_store.list_for(project.id, stage="paper", repo_root=repo)
        import logging as _logging

        review_pdf = None
        for attempt, render_math in enumerate((True, False)):
            review_tex = build_peer_review_tex(project, records, render_math=render_math)
            try:
                review_pdf = render_llmxive_pdf(
                    review_tex, work / f"review{attempt}", repo_root=repo,
                    basename="review", source_date_epoch=epoch,
                )
                break
            except Exception as exc:
                if render_math:
                    _logging.getLogger(__name__).warning(
                        "peer-review math compile failed for %s; retrying with math "
                        "as literal text: %s", project.id, exc,
                    )
                    continue
                raise
        review_target = pdf_dir / review_name
        shutil.copy2(review_pdf, review_target)
        out["peer_review"] = review_target

    return out


__all__ = [
    "build_cover_tex",
    "build_peer_review_tex",
    "build_preprint_pdfs",
    "prepend_cover_to_pdf",
    "render_llmxive_pdf",
    "resolve_original_pdf",
    "tex_escape",
]
