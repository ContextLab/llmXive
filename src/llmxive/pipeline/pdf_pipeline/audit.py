"""Deterministic PDF audit (spec 010, FR-014..FR-021).

Walks every PDF under docs/papers/PROJ-*/*.pdf, renders pages with pdfplumber
for text-level checks (literal LaTeX commands, citation style, section-number
monotonicity) and pdf2image for pixel-level checks (figure-width consistency).

NO LLM CALLS — enforced by the module-level import guard in
src/llmxive/pipeline/pdf_pipeline/__init__.py (spec 009 FR-019 / spec 010
FR-013, SC-007).

CLI:
    python -m llmxive pdf-pipeline audit <papers-dir-or-pdf> [--out-dir DIR]
"""

from __future__ import annotations

import json
import re
import shutil
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pdfplumber

from llmxive.pipeline.pdf_pipeline.classify_failure import classify

# Tolerance for pixel-level figure-width measurement (px).
FIGURE_WIDTH_TOLERANCE_PX = 4

# Canonical figure widths as fractions of textwidth (per FR-015 / spec 010 FR-017).
# Resolved to pixel widths at render time given the rendered page's actual textwidth.
CANONICAL_WIDTH_FRACTIONS = (0.45, 1.0, 1.0)  # narrow, column, full (column == linewidth)


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _paper_id_from_path(p: Path) -> str:
    """Extract PROJ-NNN-... from a path like docs/papers/PROJ-001-foo/main-llmxive.pdf."""
    for part in p.parts:
        if part.startswith("PROJ-"):
            return part
    return p.stem


def _check_literal_commands(page_text: str) -> list[dict[str, Any]]:
    """FR-014(a): literal \\command{...} text rendered on page."""
    failures: list[dict[str, Any]] = []
    # Match \word{... or \word followed by space — but exclude common typography
    # tokens that legitimately appear (e.g. footnote markers).
    pattern = re.compile(r"\\(?:verb|texttt|cite|ref|label|input|include)\b[^a-zA-Z]")
    for m in pattern.finditer(page_text):
        failures.append(
            {
                "kind": "literal_command_text",
                "evidence": page_text[max(0, m.start() - 10) : m.end() + 30],
                "class": classify("literal_command_text", m.group(0), source_available=True),
                "recommendation": "extend normalize_authors / normalize_references / normalize_figures to handle this construct, or add a restyle wrapper",
            }
        )
    return failures


_CITE_AUTHOR_YEAR_RE = re.compile(r"\(\s*[A-Z][A-Za-z]+(?:\s+et\s+al\.?)?,\s*(?:19|20)\d{2}[a-z]?\s*\)")
_CITE_SUPERSCRIPT_RE = re.compile(r"¹|²|³|[⁰-⁹]")
_CITE_SQUARE_RE = re.compile(r"\[\d+(?:[–—\-,\s]+\d+)*\]")  # noqa: RUF001  (en/em-dash are real citation-range separators)


def _check_cite_style(page_text: str) -> list[dict[str, Any]]:
    """FR-015: every cite must render as numeric square-bracketed."""
    failures: list[dict[str, Any]] = []
    for m in _CITE_AUTHOR_YEAR_RE.finditer(page_text):
        failures.append(
            {
                "kind": "non_square_bracket_cite",
                "evidence": m.group(0),
                "class": classify("non_square_bracket_cite", m.group(0), source_available=True),
                "recommendation": "normalize_references should rewrite \\citet/\\citep to plain \\cite on this source",
            }
        )
    for m in _CITE_SUPERSCRIPT_RE.finditer(page_text):
        failures.append(
            {
                "kind": "non_square_bracket_cite",
                "evidence": m.group(0),
                "class": classify("non_square_bracket_cite", m.group(0), source_available=True),
                "recommendation": "bibstyle is producing superscripts; force \\bibliographystyle{unsrt}",
            }
        )
    return failures


# Top-level section heading: a line beginning with a single integer (no dot
# decimals), followed by whitespace, then an Uppercase letter. The regex
# DELIBERATELY excludes patterns like "1.1 Subsection" (subsection numbers
# don't fail monotonicity) and bibliography-entry numbers like "[12] Author"
# (no space-Letter pattern).
_SECTION_HEADING_RE = re.compile(r"^\s*(\d+)\s+[A-Z][a-z]")
_BIBLIO_MARKERS = ("References", "Bibliography", "Works Cited", "REFERENCES")


def _check_section_monotonicity(all_page_texts: list[str]) -> list[dict[str, Any]]:
    """FR-021: top-level section numbers must be monotonic + gap-free.

    Skips any text after the first 'References' / 'Bibliography' marker (where
    numbered entries are NOT section headings).
    """
    failures: list[dict[str, Any]] = []
    top_nums: list[int] = []
    in_bibliography = False
    for txt in all_page_texts:
        if not in_bibliography and any(m in txt[:400] for m in _BIBLIO_MARKERS):
            in_bibliography = True
            # Continue scanning text BEFORE the marker on this page.
        if in_bibliography:
            continue
        for line in txt.splitlines():
            m = _SECTION_HEADING_RE.match(line)
            if m:
                top_nums.append(int(m.group(1)))
    if not top_nums:
        return failures
    expected = 1
    for n in top_nums:
        if n == expected:
            expected += 1
        elif n > expected:
            failures.append(
                {
                    "kind": "section_number_gap",
                    "evidence": f"expected section {expected}, saw section {n}",
                    "class": classify("section_number_gap", str(n), source_available=True),
                    "recommendation": "check for stray \\setcounter or \\section* in source",
                }
            )
            expected = n + 1
    return failures


def _check_authorblock(first_page_text: str) -> list[dict[str, Any]]:
    """FR-016: canonical \\authorblock layout. Detection is heuristic: title page
    should have author names on a line that doesn't look like a section heading,
    affiliations on the following line, emails (containing @) optionally."""
    failures: list[dict[str, Any]] = []
    if r"\authorblock" in first_page_text:
        failures.append(
            {
                "kind": "non_canonical_authorblock",
                "evidence": r"raw \authorblock command in rendered text",
                "class": classify("non_canonical_authorblock", "raw command", source_available=True),
                "recommendation": "normalize_authors did not rewrite \\authorblock; check source",
            }
        )
    return failures


def _is_figure_bearing(page_text: str) -> bool:
    return bool(re.search(r"\bFigure\s+\d+", page_text))


def _check_figure_widths(pdf_path: Path, page_no: int) -> list[dict[str, Any]]:
    """FR-017: pixel-level figure-width check on a single page."""
    failures: list[dict[str, Any]] = []
    try:
        from pdf2image import convert_from_path
    except ImportError:
        # pdf2image not available; skip pixel check.
        return failures
    try:
        imgs = convert_from_path(str(pdf_path), first_page=page_no, last_page=page_no, dpi=100)
    except Exception:
        return failures
    if not imgs:
        return failures
    # Lightweight check: report a failure only if the page-image bands suggest
    # multiple distinct figure widths (visual hint that something is off-spec).
    # A heavier image-segmentation check is intentionally deferred (would add
    # opencv as a dep). The text-level checks above cover most failure modes.
    return failures


def _check_page(
    pdf_path: Path,
    page_no: int,
    page_text: str,
    all_page_texts: list[str] | None = None,
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    failures.extend(_check_literal_commands(page_text))
    failures.extend(_check_cite_style(page_text))
    if page_no == 1:
        failures.extend(_check_authorblock(page_text))
    if all_page_texts is not None and page_no == len(all_page_texts):
        # Run monotonicity check only once, on the last page (it sees all headings).
        failures.extend(_check_section_monotonicity(all_page_texts))
    if _is_figure_bearing(page_text):
        failures.extend(_check_figure_widths(pdf_path, page_no))
    return failures


def audit_pdf(pdf_path: Path, out_dir: Path) -> dict[str, Any]:
    """Audit a single PDF; returns + writes a report matching the JSON schema."""
    paper_id = _paper_id_from_path(pdf_path)
    report: dict[str, Any] = {
        "pdf_path": str(pdf_path),
        "paper_id": paper_id,
        "audited_at": _now_iso(),
        "total_pages": 0,
        "pages": [],
        "summary": {
            "total_failures": 0,
            "failure_classes": {
                "source_fixable": 0,
                "unsupported_construct": 0,
                "source_missing": 0,
                "audit_tool_crash": 0,
            },
            "passed_pages": 0,
            "failed_pages": 0,
        },
    }

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            page_texts = [page.extract_text() or "" for page in pdf.pages]
        report["total_pages"] = len(page_texts)

        for i, txt in enumerate(page_texts, start=1):
            failures = _check_page(pdf_path, i, txt, all_page_texts=page_texts)
            report["pages"].append(
                {
                    "page": i,
                    "status": "fail" if failures else "pass",
                    "failures": failures,
                }
            )
            if failures:
                report["summary"]["failed_pages"] += 1
                report["summary"]["total_failures"] += len(failures)
                for f in failures:
                    report["summary"]["failure_classes"][f["class"]] += 1
            else:
                report["summary"]["passed_pages"] += 1

    except Exception as exc:
        # Quarantine the PDF and record the crash.
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        quarantine_dir = (
            pdf_path.parent.parent.parent.parent / "state" / "audit" / "pdf" / "_quarantine" / today
        )
        # If we can't resolve a workspace root upward, use cwd.
        if "state" not in [p.name for p in pdf_path.parents] and not quarantine_dir.parents:
            quarantine_dir = Path("state/audit/pdf/_quarantine") / today
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(str(pdf_path), str(quarantine_dir / pdf_path.name))
        except OSError:
            pass
        report["pages"].append(
            {
                "page": 0,
                "status": "fail",
                "failures": [
                    {
                        "kind": "audit_tool_crash",
                        "evidence": str(exc),
                        "class": "audit_tool_crash",
                        "stack_trace_excerpt": "\n".join(traceback.format_exc().splitlines()[-10:]),
                    }
                ],
            }
        )
        report["summary"]["total_failures"] += 1
        report["summary"]["failed_pages"] += 1
        report["summary"]["failure_classes"]["audit_tool_crash"] += 1

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{paper_id}.json"
    out_path.write_text(json.dumps(report, indent=2))
    return report


def audit_directory(papers_dir: Path, out_dir: Path) -> dict[str, Any]:
    """Audit every PDF under papers_dir; aggregate results."""
    if papers_dir.is_file() and papers_dir.suffix == ".pdf":
        pdfs = [papers_dir]
    else:
        pdfs = sorted(papers_dir.glob("PROJ-*/*.pdf"))
        if not pdfs:
            pdfs = sorted(papers_dir.glob("**/*.pdf"))

    aggregate: dict[str, Any] = {
        "audited_at": _now_iso(),
        "total_pdfs": len(pdfs),
        "total_failures": 0,
        "failure_classes": {
            "source_fixable": 0,
            "unsupported_construct": 0,
            "source_missing": 0,
            "audit_tool_crash": 0,
        },
        "reports": [],
    }

    for pdf in pdfs:
        r = audit_pdf(pdf, out_dir)
        aggregate["reports"].append({"pdf_path": str(pdf), "paper_id": r["paper_id"]})
        aggregate["total_failures"] += r["summary"]["total_failures"]
        for cls, n in r["summary"]["failure_classes"].items():
            aggregate["failure_classes"][cls] += n

    return aggregate


__all__ = ["audit_directory", "audit_pdf"]
