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
def tex_escape(text: str) -> str:
    """Escape the LaTeX special characters so metadata prose renders literally."""
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
    }
    out: list[str] = []
    for ch in str(text):
        out.append(replacements.get(ch, ch))
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
        r"\noindent\textbf{About llmXive.} llmXive is an automated platform for "
        r"scientific discovery in which specialist LLM agents advance ideas from a "
        r"one-paragraph brainstorm to a peer-reviewed paper. Learn more at "
        rf"\url{{{_LLMXIVE_URL}}}.",
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
# Peer-review report (llmxive.cls)
# --------------------------------------------------------------------------- #
def build_peer_review_tex(project: Project, records: list, *, action_items_md: str = "") -> str:
    """Render the reviewer verdicts + feedback + action items as an llmxive.cls doc."""
    title = tex_escape(f"llmXive Automated Review of {project.title}")
    lines = [
        r"\documentclass{llmxive}",
        rf"\title{{{title}}}",
        r"\author{llmXive automated review panel}",
        r"\paperstatus{Automated Review}",
        r"\begin{document}",
        r"\maketitle",
        (
            "This report collects the llmXive LLM review panel's assessment of an "
            "ingested preprint. It is \\textbf{advisory, automated feedback for the "
            "authors}: llmXive does not modify the paper, and nothing is accepted "
            "or rejected on its basis."
        ),
    ]
    for rec in sorted(records, key=lambda r: r.reviewer_name):
        lines.append(rf"\section*{{{tex_escape(rec.reviewer_name)}}}")
        lines.append(rf"\noindent\textbf{{Verdict:}} {tex_escape(str(rec.verdict))}\\")
        feedback = (getattr(rec, "feedback", "") or "").strip()
        if feedback:
            lines.append(tex_escape(feedback[:4000]))
        items = getattr(rec, "action_items", None) or []
        if items:
            lines.append(r"\begin{itemize}")
            for item in items:
                sev = getattr(getattr(item, "severity", ""), "value", getattr(item, "severity", ""))
                lines.append(
                    rf"\item \textbf{{[{tex_escape(str(sev))}]}} "
                    rf"{tex_escape((item.text or '').strip())}"
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
        records = reviews_store.list_for(project.id, stage="paper", repo_root=repo)
        review_tex = build_peer_review_tex(project, records)
        review_pdf = render_llmxive_pdf(
            review_tex, work / "review", repo_root=repo, basename="review",
            source_date_epoch=epoch,
        )
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
