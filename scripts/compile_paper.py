#!/usr/bin/env python3
"""Compile a project's paper to PDF.

Strategy (in order):

1. If the project has a `paper/source/` directory:
   a. If a `<base>-llmxive.tex` wrapper doesn't exist yet, run
      ``scripts/restyle_arxiv_paper.py`` to generate it.
   b. Try compiling the wrapper with lualatex (3 passes for refs +
      bibtex when a .bib exists). If that succeeds, write the PDF to
      ``paper/pdf/<base>-llmxive.pdf``.
2. If the wrapper compile fails OR there's no source dir at all, and the
   project metadata has an ``arxiv_url`` / ``arxiv_id``, fetch the
   published arXiv PDF straight from arxiv.org/pdf/<id>.pdf and write
   it to ``paper/pdf/<arxiv-id>.pdf`` so the user always has SOMETHING
   to read in the paper modal.

Idempotent + best-effort: an already-compiled PDF triggers no work; a
fallback fetch on an already-fetched PDF is a no-op (mtime-only refresh
is suppressed).

CLI:
  python scripts/compile_paper.py <project_dir>
  python scripts/compile_paper.py --all          # walks projects/*/
  python scripts/compile_paper.py --all --max 8  # limit per run
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
STYLE_DIR = REPO / "papers" / ".style"
# Use the content-extractor (clean wrapper from scratch) rather than the
# preserve-original-preamble approach, which got bogged down on venue
# .cls conflicts. See scripts/extract_paper_content.py for the rationale.
RESTYLE_SCRIPT = REPO / "scripts" / "extract_paper_content.py"
LUALATEX_PASSES = 3        # 1: write aux  2: read aux + bib  3: settle refs
COMPILE_TIMEOUT_S = 600    # per-pass timeout — a single complex paper can be slow

ARXIV_PDF_URL = "https://arxiv.org/pdf/{arxiv_id}.pdf"


def _load_metadata(project: Path) -> dict[str, Any]:
    p = project / "paper" / "metadata.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _pdf_dir(project: Path) -> Path:
    d = project / "paper" / "pdf"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _has_pdf(project: Path) -> bool:
    """True iff at least one valid MAIN .pdf (with EOF trailer) exists under
    paper/pdf/. A 2KB error stub written by a failing lualatex run does
    NOT count — we want to re-attempt compile/fallback for those.

    Excludes supplement-llmxive.pdf and similar non-main PDFs from this
    check. A paper with only a supplement on disk must still recompile
    its main paper PDF — without this exclusion, PROJ-562's supplement
    was masking the missing main PDF and the compile-all loop skipped
    it as 'already-present'.
    """
    for p in (project / "paper" / "pdf").glob("*.pdf"):
        # Skip non-main artifacts. The main PDF is named either
        # `main-llmxive.pdf` (canonical) or `<arxiv-id>.pdf` (fallback).
        # Anything else (supplement-llmxive.pdf, etc.) is auxiliary and
        # doesn't satisfy the "this project has a compiled paper" check.
        if p.name.startswith("supplement"):
            continue
        try:
            data = p.read_bytes()
        except Exception:
            continue
        if b"%%EOF" in data[-1024:] and len(data) > 4096:
            return True
    return False


def _entry_tex(project: Path, metadata: dict[str, Any]) -> str | None:
    """Pick the entry-point .tex from metadata.toplevel_tex if present,
    otherwise sniff the source dir for a single .tex with `\\documentclass`.
    """
    tops = metadata.get("toplevel_tex") or []
    if isinstance(tops, list) and tops:
        for name in tops:
            if (project / "paper" / "source" / name).is_file():
                return name
    src = project / "paper" / "source"
    if not src.is_dir():
        return None
    candidates: list[Path] = []
    for tex in sorted(src.glob("*.tex")):
        text = tex.read_text(encoding="utf-8", errors="replace")
        if r"\documentclass" in text:
            candidates.append(tex)
    if len(candidates) == 1:
        return candidates[0].name
    # Multiple candidates — try common conventions
    for name in ("main.tex", "ms.tex", "paper.tex"):
        if (src / name).is_file():
            return name
    return candidates[0].name if candidates else None


def _restyle_if_needed(project: Path, metadata: dict[str, Any], entry: str) -> Path | None:
    """Run restyle_arxiv_paper.py to produce main-llmxive.tex if missing."""
    src = project / "paper" / "source"
    wrapper = src / "main-llmxive.tex"
    if wrapper.is_file():
        return wrapper
    arxiv_id = (metadata.get("arxiv_id") or "").strip()
    if not arxiv_id:
        # Synthesize one from the project id so the metadata block isn't empty
        arxiv_id = project.name
    args = [
        sys.executable, str(RESTYLE_SCRIPT),
        str(src), entry,
        "--out", "main-llmxive.tex",
        "--arxiv-id", arxiv_id,
    ]
    proc = subprocess.run(args, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        print(f"[compile] restyle failed for {project.name}: {proc.stderr.strip()}",
              file=sys.stderr)
        return None
    return wrapper if wrapper.is_file() else None


def _clean_partial_outputs(pdf_dir: Path, base: str) -> None:
    """Remove leftover .pdf/.log/.aux from a previous failed compile so a
    later run isn't fooled by a 0-byte stub."""
    for suffix in (".pdf", ".log", ".aux", ".out", ".toc", ".bbl", ".blg"):
        p = pdf_dir / f"{base}{suffix}"
        if p.is_file():
            try:
                p.unlink()
            except OSError:
                pass


def _run_lualatex(project: Path, wrapper: Path) -> tuple[bool, str]:
    """Run lualatex N times from the repo root. Returns (success, log_tail)."""
    if not shutil.which("lualatex"):
        return False, "lualatex not on PATH"
    src = wrapper.parent
    pdf_dir = _pdf_dir(project)
    # Wipe any leftover artifacts from a previous failed compile.
    _clean_partial_outputs(pdf_dir, wrapper.stem)
    env_path = f"{src}:{STYLE_DIR}:"   # trailing colon = append default
    # BIBINPUTS lets bibtex find .bib files; BSTINPUTS for .bst styles.
    # Both point at the source dir so foo.bib / splncs04.bst etc. resolve.
    bib_path = f"{src}:"
    bst_path = f"{src}:"
    env = {
        **dict(__import__("os").environ),
        "TEXINPUTS": env_path,
        "BIBINPUTS": bib_path,
        "BSTINPUTS": bst_path,
    }
    last_tail = ""
    has_bib = any(src.glob("*.bib"))
    for i in range(1, LUALATEX_PASSES + 1):
        cmd = [
            "lualatex", "-interaction=nonstopmode",
            "-halt-on-error=false",
            "-output-directory", str(pdf_dir),
            str(wrapper),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              cwd=str(REPO), env=env, timeout=COMPILE_TIMEOUT_S)
        last_tail = (proc.stdout or "").splitlines()[-30:]
        last_tail = "\n".join(last_tail)
        # Between passes 1 and 2, run bibtex if a .bib exists. bibtex
        # opens auxiliary files relative to cwd, so we run it FROM the
        # pdf_dir (where the .aux lives), with BIBINPUTS pointing at the
        # source dir where the .bib lives. Both stdout AND stderr are
        # captured so we can surface bibtex errors in the log tail.
        if i == 1 and has_bib:
            base = wrapper.stem
            aux_path = pdf_dir / f"{base}.aux"
            if aux_path.is_file():
                bproc = subprocess.run(
                    ["bibtex", base],
                    capture_output=True, text=True,
                    cwd=str(pdf_dir), env=env,
                    timeout=120,
                )
                # Surface bibtex output into last_tail so failures are
                # diagnosable from the result dict.
                bib_out = (bproc.stdout or "") + (bproc.stderr or "")
                if bib_out.strip():
                    last_tail = last_tail + "\n--bibtex--\n" + bib_out[-1500:]
    out_pdf = pdf_dir / f"{wrapper.stem}.pdf"
    # A "fatal error" PDF written by lualatex can still be tiny / empty.
    # Require a valid trailer to consider the compile successful; on
    # failure, wipe the stub so the arXiv fallback's PDF is the only
    # file left in paper/pdf/.
    if not out_pdf.is_file():
        return False, last_tail
    try:
        data = out_pdf.read_bytes()
        if not data or b"%%EOF" not in data[-1024:]:
            _clean_partial_outputs(pdf_dir, wrapper.stem)
            return False, last_tail
    except Exception:
        _clean_partial_outputs(pdf_dir, wrapper.stem)
        return False, last_tail
    return True, last_tail


def _scan_overflow_warnings(pdf_dir: Path, base: str, *, threshold_pt: float = 50.0) -> list[dict]:
    """Scan the lualatex log for severe Overfull \\hbox warnings.

    Anything over `threshold_pt` (default: 50pt — about 8mm at A4) is
    bad enough to suggest the figure/table overflowed the page rather
    than just nudging slightly past the column. Returns a list of
    {amount_pt, lines_range} dicts. An empty list means the document
    looks clean.

    The workflow can surface this as a per-project warning so a human
    can act on the bad figure — wrapfigure conversion already handles
    the most common cause but graphics with their own \\includegraphics
    sizing can still overflow.
    """
    log_path = pdf_dir / f"{base}.log"
    if not log_path.is_file():
        return []
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    pat = re.compile(
        r"Overfull \\hbox \(([\d.]+)pt too wide\) in paragraph at lines (\S+)",
    )
    out: list[dict] = []
    for m in pat.finditer(text):
        try:
            amt = float(m.group(1))
        except ValueError:
            continue
        if amt >= threshold_pt:
            out.append({"amount_pt": amt, "lines": m.group(2)})
    return out


def _fetch_arxiv_fallback(project: Path, arxiv_id: str) -> Path | None:
    """Download the canonical arXiv PDF as a fallback when the restyle
    compile fails. Returns the on-disk path or None.
    """
    if not arxiv_id:
        return None
    url = ARXIV_PDF_URL.format(arxiv_id=arxiv_id)
    out = _pdf_dir(project) / f"{arxiv_id}.pdf"
    if out.is_file() and out.stat().st_size > 1024:
        return out  # already fetched
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "llmxive-compile/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
    except Exception as exc:
        print(f"[compile] arxiv-fallback failed for {project.name}: {exc}",
              file=sys.stderr)
        return None
    if not data or len(data) < 1024:
        return None
    out.write_bytes(data)
    return out


def compile_project(project: Path) -> dict[str, Any]:
    """Try to produce at least one PDF under project/paper/pdf/.

    Returns a result dict for logging. Always best-effort — never raises.
    """
    result: dict[str, Any] = {"project": project.name, "ok": False,
                              "strategy": None, "pdf": None, "errors": []}
    if _has_pdf(project):
        result.update(ok=True, strategy="already-present",
                      pdf=str(next((project / "paper" / "pdf").glob("*.pdf"))))
        return result

    metadata = _load_metadata(project)
    src = project / "paper" / "source"
    arxiv_id = (metadata.get("arxiv_id") or "").strip()

    if src.is_dir():
        entry = _entry_tex(project, metadata)
        if entry is None:
            result["errors"].append("no entry .tex found in paper/source/")
        else:
            wrapper = _restyle_if_needed(project, metadata, entry)
            if wrapper is None:
                result["errors"].append("restyle step failed")
            else:
                ok, tail = _run_lualatex(project, wrapper)
                if ok:
                    pdf = _pdf_dir(project) / f"{wrapper.stem}.pdf"
                    # Scan the lualatex log for severe Overfull warnings —
                    # boxes >50pt too wide almost always mean a figure or
                    # table overflowed the page. The compile itself
                    # succeeds, but we want to surface these so a human can
                    # diagnose without manually grepping the .log.
                    overflow = _scan_overflow_warnings(_pdf_dir(project), wrapper.stem)
                    result.update(ok=True, strategy="llmxive-compile",
                                  pdf=str(pdf), overflow=overflow)
                    return result
                else:
                    result["errors"].append(f"lualatex failed:\n{tail[-2000:]}")

    if arxiv_id:
        pdf = _fetch_arxiv_fallback(project, arxiv_id)
        if pdf is not None:
            result.update(ok=True, strategy="arxiv-fallback", pdf=str(pdf))
            return result
        result["errors"].append("arxiv-fallback fetch failed")
    else:
        result["errors"].append("no arxiv_id in metadata — no fallback available")
    return result


def _iter_projects(arg_dirs: list[Path]) -> list[Path]:
    """Resolve --all + explicit project paths into a deduped list."""
    seen: set[Path] = set()
    out: list[Path] = []
    for p in arg_dirs:
        p = p.resolve()
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="compile_paper.py",
                                 description=__doc__.split("\n", 1)[0])
    ap.add_argument("project_dir", nargs="*", type=Path,
                    help="One or more project dirs (projects/PROJ-NNN-...)")
    ap.add_argument("--all", action="store_true",
                    help="Compile every project under projects/ missing a PDF.")
    ap.add_argument("--max", type=int, default=None,
                    help="With --all, cap how many to attempt per run.")
    args = ap.parse_args(argv)

    if args.all:
        all_projects = sorted([p for p in (REPO / "projects").iterdir() if p.is_dir()])
        targets = [p for p in all_projects if (p / "paper" / "source").is_dir() and not _has_pdf(p)]
        if args.max:
            targets = targets[: args.max]
    else:
        targets = _iter_projects(args.project_dir)

    if not targets:
        print("[compile] no projects to compile")
        return 0

    fail_count = 0
    for project in targets:
        res = compile_project(project)
        if res["ok"]:
            print(f"[compile] {project.name}: {res['strategy']} → {Path(res['pdf']).name}")
            # Surface page-overflow warnings — these don't fail the
            # compile but mean a figure/table is wider than the page.
            for w in (res.get("overflow") or []):
                print(f"  ⚠ overflow {w['amount_pt']:.0f}pt at lines {w['lines']}",
                      file=sys.stderr)
        else:
            fail_count += 1
            print(f"[compile] {project.name}: FAILED", file=sys.stderr)
            for err in res["errors"]:
                print(f"  {err.splitlines()[0]}", file=sys.stderr)
    # Per project failures are reported; the run itself succeeds (the
    # workflow will keep retrying on subsequent ticks).
    return 0 if not fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
