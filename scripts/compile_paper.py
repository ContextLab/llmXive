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
sys.path.insert(0, str(REPO / "src"))
STYLE_DIR = REPO / "papers" / ".style"
# Use the content-extractor (clean wrapper from scratch) rather than the
# preserve-original-preamble approach, which got bogged down on venue
# .cls conflicts. See scripts/extract_paper_content.py for the rationale.
RESTYLE_SCRIPT = REPO / "scripts" / "extract_paper_content.py"
LUALATEX_PASSES = 3        # 1: write aux  2: read aux + bib  3: settle refs
# Per-pass timeout. 600s occasionally starved genuinely-large papers; 900s
# (15 min) gives real headroom while staying within the CI job budget.
# Note the dominant historical "hang" (PROJ-683, >30 min) was NOT slowness
# but a pathological `\allowbreak` density under lualatex+OpenType — fixed
# at the source in extract_paper_content._strip_dense_allowbreak, so this
# ceiling is now a backstop, not a load-bearing budget.
COMPILE_TIMEOUT_S = 900
# Bounded llmxive-restyle retries for a paper already serving its arXiv
# fallback. Each scheduled sweep may re-attempt the themed compile until this
# many failures are recorded (paper_status.llmxive_compile_attempts); after
# that the paper is an honest `compile-exhausted` skip — the fallback keeps
# serving, the status record carries why, and a human can reset the counter
# after fixing the source. Without the cap a permanently-hanging source would
# burn COMPILE_TIMEOUT_S on every sweep forever; without the RETRY the old
# `_has_pdf` gate made the first fallback PERMANENT (a fallback PDF counted as
# "compiled", so the paper was never restyled into the llmxive theme — the
# PROJ-669/671 class).
MAX_LLMXIVE_COMPILE_ATTEMPTS = 3

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


def _has_llmxive_pdf(project: Path) -> bool:
    """True iff the CANONICAL restyled main-llmxive.pdf exists and is valid.

    Defect (PROJ-669/671 class): `_has_pdf` also accepts the `<arxiv-id>.pdf`
    FALLBACK, which is correct for "something renders in the modal" but must
    not mean "this paper is done" — a fallback-only paper still needs the
    llmxive-theme restyle on later sweeps (bounded by
    MAX_LLMXIVE_COMPILE_ATTEMPTS).
    """
    p = project / "paper" / "pdf" / "main-llmxive.pdf"
    try:
        data = p.read_bytes()
    except Exception:
        return False
    return b"%%EOF" in data[-1024:] and len(data) > 4096


def _llmxive_attempts(project: Path) -> int:
    """Read the persisted failed-restyle attempt count from paper_status."""
    try:
        from llmxive.state.paper_status import load as _load_status
        rec = _load_status(project.name, repo_root=REPO) or {}
        n = rec.get("llmxive_compile_attempts", 0)
        return int(n) if isinstance(n, int) and n >= 0 else 0
    except Exception:
        return 0


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
    """Run restyle_arxiv_paper.py to produce main-llmxive.tex if missing
    OR stale.

    Staleness rule: if the wrapper exists but the extract script
    (`scripts/extract_paper_content.py`) is newer, regenerate. This
    protects against the silent regression that bit PROJ-571: a fix to
    the wrapper-generator landed but old wrappers kept compiling with
    the unfixed bug intact (we patched `\\@onedot` handling, but the
    pre-existing `\\providecommand{...}` line in the wrapper was still
    leaking 'nedot.' above the title).
    """
    src = project / "paper" / "source"
    wrapper = src / "main-llmxive.tex"
    if wrapper.is_file():
        try:
            wrapper_mtime = wrapper.stat().st_mtime
            script_mtime = RESTYLE_SCRIPT.stat().st_mtime
            if wrapper_mtime >= script_mtime:
                return wrapper
            print(f"[compile] wrapper stale (script newer) — regenerating "
                  f"{wrapper.relative_to(REPO)}", file=sys.stderr)
        except OSError:
            return wrapper  # mtime read failed → just reuse
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


def _install_precompiled_bbl(src: Path, pdf_dir: Path, wrapper_stem: str) -> Path | None:
    """When the arXiv tarball ships a pre-compiled `.bbl` but no `.bib`
    (a common practice — bibliographies arrive resolved), bibtex can't
    run and lualatex can't find a `.bbl` matching the wrapper's stem.
    The result: natbib renders every `\\cite{...}` as `[?]`.

    Symptom seen in the wild: PROJ-576 (SANA-WM) had `[? ? ? ? ?]`
    throughout its Introduction.

    Fix: copy the source `.bbl` into `pdf_dir`, renamed to
    `{wrapper_stem}.bbl` so lualatex picks it up by name. Returns the
    destination path on success, or None when no source `.bbl` exists.
    """
    src_bbl_candidates = list(src.glob("*.bbl"))
    if not src_bbl_candidates:
        return None
    # Prefer `main.bbl` over alternates, otherwise the first.
    src_bbl = next(
        (p for p in src_bbl_candidates if p.stem == "main"),
        src_bbl_candidates[0],
    )
    pdf_dir.mkdir(parents=True, exist_ok=True)
    dst_bbl = pdf_dir / f"{wrapper_stem}.bbl"
    try:
        shutil.copy2(src_bbl, dst_bbl)
    except OSError as exc:
        print(f"[compile] could not copy {src_bbl} → {dst_bbl}: {exc}",
              file=sys.stderr)
        return None
    return dst_bbl


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
    if not has_bib:
        _install_precompiled_bbl(src, pdf_dir, wrapper.stem)
    for i in range(1, LUALATEX_PASSES + 1):
        cmd = [
            "lualatex", "-interaction=nonstopmode",
            "-halt-on-error=false",
            "-output-directory", str(pdf_dir),
            str(wrapper),
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  cwd=str(REPO), env=env, timeout=COMPILE_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            # A hung TeX run (infinite macro loop, interactive prompt slipped
            # through nonstopmode, …) is a COMPILE FAILURE for this paper —
            # not a lane-killer. The uncaught TimeoutExpired previously
            # crashed the whole sweep, so every scheduled run died at the
            # same poisoned paper and everything queued behind it never got
            # restyled (the systemic cause of the missing themed PDFs).
            _clean_partial_outputs(pdf_dir, wrapper.stem)
            return False, (
                f"lualatex timed out after {COMPILE_TIMEOUT_S}s on pass {i} "
                "(hung TeX run — likely an infinite loop in the source)"
            )
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
                try:
                    bproc = subprocess.run(
                        ["bibtex", base],
                        capture_output=True, text=True,
                        cwd=str(pdf_dir), env=env,
                        timeout=120,
                    )
                except subprocess.TimeoutExpired:
                    last_tail += "\n--bibtex--\nbibtex timed out after 120s"
                else:
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


_UNREADABLE_PDF_RE = re.compile(
    r"\(file ([^)]+\.pdf)\) \(pdf inclusion\): reading image failed"
)


def _repair_unreadable_pdf_assets(project: Path, log_tail: str) -> list[Path]:
    """Ghostscript-rewrite figure PDFs lualatex could not embed.

    Returns the list of repaired paths (empty when nothing matched / gs
    missing / rewrite failed). The original is kept as ``<name>.orig``.
    """
    import shutil
    repaired: list[Path] = []
    gs = shutil.which("gs")
    if not gs:
        return repaired
    src = project / "paper" / "source"
    # TeX wraps log lines at ~79 columns, splitting the message (and even
    # the filename) mid-word — de-wrap before matching.
    dewrapped = (log_tail or "").replace("\n", "")
    for m in _UNREADABLE_PDF_RE.finditer(dewrapped):
        rel = m.group(1).strip()
        asset = (src / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
        if not asset.is_file():
            continue
        backup = asset.with_suffix(asset.suffix + ".orig")
        tmp = asset.with_suffix(".gsfix.pdf")
        proc = subprocess.run(
            [gs, "-q", "-o", str(tmp), "-sDEVICE=pdfwrite", str(asset)],
            capture_output=True, text=True, timeout=120,
        )
        if proc.returncode == 0 and tmp.is_file() and tmp.stat().st_size > 1024:
            if not backup.exists():
                asset.rename(backup)
            tmp.rename(asset)
            repaired.append(asset)
            print(f"[compile] gs-repaired unreadable figure: {asset.name}")
        else:
            tmp.unlink(missing_ok=True)
    return repaired


def compile_project(project: Path) -> dict[str, Any]:
    """Try to produce at least one PDF under project/paper/pdf/.

    Returns a result dict for logging. Always best-effort — never raises.
    """
    result: dict[str, Any] = {"project": project.name, "ok": False,
                              "strategy": None, "pdf": None, "errors": []}
    if _has_llmxive_pdf(project):
        result.update(ok=True, strategy="already-present",
                      pdf=str(project / "paper" / "pdf" / "main-llmxive.pdf"))
        return result
    # A fallback-only paper is SERVING but not DONE: re-attempt the themed
    # compile until the bounded attempt budget is exhausted, then skip
    # honestly (the fallback stays; the status record carries why).
    fallback_only = _has_pdf(project)
    if fallback_only and _llmxive_attempts(project) >= MAX_LLMXIVE_COMPILE_ATTEMPTS:
        result.update(
            ok=True, strategy="compile-exhausted",
            pdf=str(next((project / "paper" / "pdf").glob("*.pdf"))),
            errors=[
                f"llmxive restyle failed {MAX_LLMXIVE_COMPILE_ATTEMPTS}x — "
                "serving the arXiv fallback; reset llmxive_compile_attempts "
                "in state/paper_status/ after fixing the source"
            ],
        )
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
                result["llmxive_attempted"] = True
                ok, tail = _run_lualatex(project, wrapper)
                if not ok:
                    # Self-heal: lualatex's pdf-inclusion reader chokes on
                    # some valid-per-pdfinfo assets ("(pdf inclusion):
                    # reading image failed" — PROJ-655's
                    # scale_out_teaser.pdf). A ghostscript pdfwrite
                    # round-trip normalizes the asset; repair every named
                    # offender once and retry the compile.
                    repaired = _repair_unreadable_pdf_assets(project, tail)
                    if repaired:
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

    if fallback_only:
        # The fallback PDF is already on disk — keep serving it; the recorded
        # errors (and llmxive_attempted) carry why the themed compile failed.
        result.update(ok=True, strategy="arxiv-fallback",
                      pdf=str(next((project / "paper" / "pdf").glob("*.pdf"))))
        return result
    if arxiv_id:
        pdf = _fetch_arxiv_fallback(project, arxiv_id)
        if pdf is not None:
            result.update(ok=True, strategy="arxiv-fallback", pdf=str(pdf))
            return result
        result["errors"].append("arxiv-fallback fetch failed")
    else:
        result["errors"].append("no arxiv_id in metadata — no fallback available")
    return result


def _record_status(project: Path, result: dict[str, Any]) -> None:
    """Spec 023 / FR-022: every compile/restyle outcome writes the per-paper
    status record — a fallback (or failure) without a recorded reason is a
    contract violation. Best-effort: a status-write failure never breaks
    the compile sweep, but it is LOUD."""
    try:
        from llmxive.state.paper_status import record_compile_result

        record_compile_result(project.name, result, repo_root=REPO)
    except Exception as exc:
        print(f"[compile] WARNING: paper-status record failed for "
              f"{project.name}: {exc}", file=sys.stderr)


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
        # Fallback-only papers stay in the sweep (the per-project attempt
        # budget bounds the cost) — only a valid CANONICAL main-llmxive.pdf
        # means "done". The old `not _has_pdf` filter made the first arXiv
        # fallback permanent (PROJ-669/671 class).
        targets = [
            p for p in all_projects
            if (p / "paper" / "source").is_dir() and not _has_llmxive_pdf(p)
        ]
        if args.max:
            targets = targets[: args.max]
    else:
        targets = _iter_projects(args.project_dir)

    if not targets:
        print("[compile] no projects to compile")
        return 0

    fail_count = 0
    for project in targets:
        # The sweep must survive ANY single project — compile_project's
        # "never raises" contract was violated by an uncaught
        # subprocess.TimeoutExpired, which killed every scheduled run at the
        # same hung paper and starved the whole queue behind it.
        try:
            res = compile_project(project)
        except Exception as exc:
            res = {"project": project.name, "ok": False, "strategy": None,
                   "pdf": None,
                   "errors": [f"compile_project raised {type(exc).__name__}: {exc}"]}
        _record_status(project, res)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
