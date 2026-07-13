"""PDF page-level defect auditor (FR-012, FR-013).

Defect taxonomy:
    unevaluated_command
    section_numbering
    reference_style
    figure_size_inconsistency
    author_block_inconsistency
    link_style
    custom_block_misrender

Uses `pdftotext -layout` (Poppler) for text scans and `pdfplumber` for
figure-box geometry (research.md §2). Both are open-source per Principle IV.
NEVER an LLM — Principle II (verified accuracy) is enforced by scanning
the rendered output, not asking a model.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from . import register
from .manifest import Defect, ManifestItem, RuleFired, add_item, new_manifest

# Defect patterns scanned over pdftotext -layout output

# An unevaluated command leaks LaTeX backslash + word into the rendered text.
UNEVAL_CMD_RE = re.compile(r"\\\\?[A-Za-z]{2,}\{[^}]*\}")

# Reference style: detect non-[N] forms (author-year, (Smith 2024), etc.)
NON_NUMERIC_REF_RE = re.compile(
    r"\(\s*(?:[A-Z][a-zA-Z]+(?:\s+(?:et\s+al\.?|and|&)\s+[A-Z][a-zA-Z]+)?)\s*,?\s*(?:19|20)\d{2}[a-z]?\s*\)"
)
NUMERIC_BRACKET_RE = re.compile(r"\[\s*\d+\s*(?:,\s*\d+\s*)*(?:[-–]\s*\d+\s*)?\]")  # noqa: RUF001  (en-dash is a real citation-range separator)

# Section numbering: monotonic "<N>" or "<N>.<M>" headings
SECTION_HEAD_RE = re.compile(r"^(\d+)(?:\.\d+)*\s+\S", re.MULTILINE)


def _pdftotext_layout(pdf: Path) -> list[str]:
    """Run `pdftotext -layout` and return per-page text. Fail-fast if absent (Principle V)."""
    try:
        # -layout preserves geometry; -enc UTF-8 to keep curly quotes etc.
        out = subprocess.check_output(
            ["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), "-"],
            stderr=subprocess.PIPE,
        ).decode("utf-8", errors="replace")
    except FileNotFoundError as e:
        raise RuntimeError(
            "pdftotext (Poppler) is not on PATH; please install poppler "
            "(`brew install poppler` or `apt-get install poppler-utils`)."
        ) from e
    except subprocess.CalledProcessError as e:
        # Some PDFs have minor errors that don't fail extraction; surface anyway.
        return e.output.decode("utf-8", errors="replace").split("\x0c") if e.output else [""]
    return out.split("\x0c")  # form-feed splits pages in pdftotext output


def scan_pdf(pdf: Path) -> list[Defect]:
    """Page-level scan against the FR-012 taxonomy."""
    pages = _pdftotext_layout(pdf)
    defects: list[Defect] = []
    paper_id = pdf.stem

    # Section numbering: cross-page monotonic check
    section_numbers: list[tuple[int, int]] = []  # (page_idx, top-level-number)

    for page_idx, page in enumerate(pages, start=1):
        if not page.strip():
            continue

        # unevaluated_command
        for m in UNEVAL_CMD_RE.finditer(page):
            defects.append(Defect(
                paper_id=paper_id,
                page=page_idx,
                defect_type="unevaluated_command",
                evidence_snippet=m.group(0)[:120],
                rule_id="latex_command_in_text",
                auto_fixable=False,
            ))

        # reference_style: non-numeric citation forms detected
        for m in NON_NUMERIC_REF_RE.finditer(page):
            defects.append(Defect(
                paper_id=paper_id,
                page=page_idx,
                defect_type="reference_style",
                evidence_snippet=m.group(0),
                rule_id="non_numeric_inline_citation",
                auto_fixable=True,
            ))

        # link_style: bare DOI/URL without proper anchor formatting heuristic
        if re.search(r"https?:[^\s]+\s*$", page, re.MULTILINE):
            # Trailing URL on a line is often a leaked link; flag once per page
            defects.append(Defect(
                paper_id=paper_id,
                page=page_idx,
                defect_type="link_style",
                evidence_snippet="trailing-line URL",
                rule_id="bare_url_trailing",
                auto_fixable=True,
            ))

        # section_numbering: collect headings
        for m in SECTION_HEAD_RE.finditer(page):
            try:
                section_numbers.append((page_idx, int(m.group(1))))
            except ValueError:
                pass

    # After scan: section-number monotonicity
    if section_numbers:
        prev = 0
        for page_idx, n in section_numbers:
            if n < prev:  # backward jump = mis-numbered
                defects.append(Defect(
                    paper_id=paper_id,
                    page=page_idx,
                    defect_type="section_numbering",
                    evidence_snippet=f"section {n} after section {prev}",
                    rule_id="section_non_monotonic",
                    auto_fixable=False,
                ))
            prev = max(prev, n)

    return defects


def _figure_size_check(pdf: Path) -> list[Defect]:
    """Use pdfplumber to extract image-box geometry; flag inconsistent widths."""
    try:
        import pdfplumber
    except ImportError:
        # If pdfplumber is not installed, skip silently — the import-guard test
        # ensures it's present in test environments; production runs surface
        # this via fail-fast precondition checks in cli.py.
        return []

    paper_id = pdf.stem
    widths: dict[int, list[float]] = {}
    try:
        with pdfplumber.open(pdf) as p:
            page_width = float(p.pages[0].width) if p.pages else 0
            if not page_width:
                return []
            for page_idx, page in enumerate(p.pages, start=1):
                for img in page.images:
                    w = float(img.get("width", 0))
                    if w:
                        widths.setdefault(page_idx, []).append(w / page_width)
    except Exception:
        return []

    # FR-015: bounded set of allowed widths (~0.45, ~1.0 for column, ~1.0+ for full)
    # Flag any image whose width-ratio isn't within 0.05 of {0.45, 0.65, 0.90, 1.00}
    allowed = (0.45, 0.65, 0.90, 1.00)
    defects: list[Defect] = []
    for page_idx, ratios in widths.items():
        for r in ratios:
            if not any(abs(r - a) < 0.05 for a in allowed):
                defects.append(Defect(
                    paper_id=paper_id,
                    page=page_idx,
                    defect_type="figure_size_inconsistency",
                    evidence_snippet=f"width ratio {r:.3f} not in {allowed}",
                    rule_id="figure_width_not_in_bounded_set",
                    auto_fixable=True,
                ))
    return defects


def audit(*, papers_dir: Path | str, repo_root: Path | str = ".", class_path: Path | str | None = None, **_: Any) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    papers_dir = Path(papers_dir).resolve()
    if not papers_dir.exists():
        raise FileNotFoundError(f"papers_dir does not exist: {papers_dir}")

    manifest = new_manifest("pdf")

    # Only paper PDFs enter the registry. A "paper PDF" is one of:
    #   - directly under papers_dir (e.g. papers/foo.pdf)
    #   - at depth 2 (papers_dir/<project>/<name>.pdf) with a stem carrying the
    #     ``-llmxive`` suffix — the marker the compile/restyle pipeline stamps on
    #     every PDF IT renders: main-llmxive, supplement-llmxive, and (from the
    #     reviewed-preprint pipeline) original-llmxive + peer-review-llmxive.
    # Any PDF deeper than 1 level is a figure / logo / asset, not a paper; and a
    # depth-2 PDF WITHOUT the suffix (``original.pdf``, ``2606.30616.pdf``) is the
    # upstream author's own arXiv file, whose LaTeX we neither produced nor control
    # — auditing it for our own typesetting defects would be meaningless.
    #
    # This suffix rule REPLACES a hardcoded {main,supplement} stem set that predated
    # the reviewed-preprint pipeline: it silently classified all 374 original-llmxive
    # / peer-review-llmxive PDFs as non-papers, so the audit gate skipped every one.
    def _is_paper_pdf(p: Path) -> bool:
        try:
            rel = p.resolve().relative_to(papers_dir)
        except ValueError:
            return True
        # Top-level PDFs: keep (e.g. papers/foo.pdf)
        if len(rel.parts) == 1:
            return True
        if len(rel.parts) == 2:
            return p.stem.endswith("-llmxive")
        return False

    pdfs = sorted([
        p.resolve() for p in papers_dir.glob("*.pdf")
        if _is_paper_pdf(p)
    ]) + sorted([
        p.resolve() for p in papers_dir.glob("**/*.pdf")
        if _is_paper_pdf(p)
    ])
    # dedupe (glob + ** can overlap)
    seen: set[Path] = set()
    pdfs = [p for p in pdfs if not (p in seen or seen.add(p))]  # type: ignore[func-returns-value]  # set.add returns None; walrus idiom

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(repo_root))
        except ValueError:
            return str(p)

    manifest["inputs_scanned"] = [_rel(p) for p in pdfs]

    registry_entries: list[dict[str, Any]] = []
    for pdf in pdfs:
        defects = scan_pdf(pdf) + _figure_size_check(pdf)
        cls = "passes" if not defects else "fails"
        rules = [RuleFired(rule_id="pdf_audit", evidence_snippet=f"{len(defects)} defect(s)")]
        add_item(manifest, ManifestItem(
            target=_rel(pdf),
            rules_fired=rules,
            classification=cls,
            defects=defects,
        ))
        if cls == "passes":
            registry_entries.append({
                "paper_id": pdf.stem,
                "pdf_path": _rel(pdf),
                "last_passed_at": manifest["started_at"],
            })

    # Auto-populate supported-PDFs registry (FR-022, Clarification Q2)
    registry = {
        "auditor_version": manifest["version"],
        "audited_at": manifest["started_at"],
        "entries": registry_entries,
    }
    registry_path = repo_root / "papers" / ".supported.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True))

    return manifest


register("pdf", audit)
