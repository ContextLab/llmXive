#!/usr/bin/env python3
"""Audit Overfull \\hbox/\\vbox warnings across every compiled paper.

The llmXive paper pipeline compiles each project's restyled wrapper with
lualatex (see scripts/compile_paper.py). lualatex records every line of
content that is too wide (\\hbox) or too tall (\\vbox) for the page in the
`.log`. This tool walks those logs and reports the overflows, CLASSIFIED by
what kind of content overflowed — so a human (or the pipeline) can tell at a
glance whether the remaining overflow is a wide table, an unwrapped code
block, a venue page-banner, a custom callout box, or just a long-token
paragraph, and target a GENERAL fix accordingly.

It reads already-compiled logs by default (fast, no LaTeX needed). Pass
``--compile`` to (re)compile any paper missing a fresh log first.

Usage:
  python scripts/audit_overflows.py                  # all projects
  python scripts/audit_overflows.py --min-pt 50      # only >=50pt
  python scripts/audit_overflows.py --compile        # compile missing first
  python scripts/audit_overflows.py PROJ-571 PROJ-606
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

OVERFULL_RE = re.compile(
    r"Overfull \\(hbox|vbox) \(([\d.]+)pt too (?:wide|high)\)"
    r"(?:.*?at lines (\d+)--(\d+))?",
    re.S,
)
_ENV_OPEN = re.compile(r"\\begin\s*\{([A-Za-z*]+)\}")
_ENV_CLOSE = re.compile(r"\\end\s*\{([A-Za-z*]+)\}")

TABLE_ENVS = {"table", "table*", "tabular", "tabular*", "tabularx", "tabulary",
              "longtable", "longtblr", "tblr", "array", "supertabular", "NiceTabular"}
FIG_ENVS = {"figure", "figure*", "wrapfigure", "wraptable", "SCfigure"}
CODE_ENVS = {"lstlisting", "lstlisting*", "verbatim", "Verbatim", "minted", "alltt",
             "promptbox", "tcblisting"}
MATH_ENVS = {"equation", "equation*", "align", "align*", "gather", "gather*",
             "multline", "multline*", "displaymath", "eqnarray", "eqnarray*",
             "alignat", "alignat*", "flalign"}
BOX_ENVS = {"tcolorbox", "mdframed", "framed", "shadowbox", "promptbox"}


def _classify(lines: list[str], a: int, b: int, kind: str) -> str:
    if a == 0:
        return "page-output (vbox)" if kind == "vbox" else "page-output (hbox)"
    window = "\n".join(lines[max(0, a - 1):b])
    if "```" in window:
        return "markdown-code"
    if re.search(r"\\AddToShipoutPicture|makebox\s*\[\s*\\paperwidth", window):
        return "shipout-banner"
    depth: dict[str, int] = defaultdict(int)
    for ln in range(a - 1, max(-1, a - 400), -1):
        if not (0 <= ln < len(lines)):
            continue
        text = lines[ln]
        for m in _ENV_CLOSE.finditer(text):
            depth[m.group(1)] += 1
        for m in _ENV_OPEN.finditer(text):
            env = m.group(1)
            if depth[env] > 0:
                depth[env] -= 1
            else:
                if env in CODE_ENVS:
                    return "code/listing"
                if env in TABLE_ENVS:
                    return "table"
                if env in MATH_ENVS:
                    return "math (display)"
                if env in FIG_ENVS:
                    return "figure"
                if env in BOX_ENVS:
                    return "callout-box"
                if env not in {"document", "abstract"}:
                    return f"env:{env}"
    if re.search(r"\\(?:url|href|path)\b|https?://", window):
        return "long-url"
    return "paragraph"


def _projects(args_dirs: list[str]) -> list[Path]:
    root = REPO / "projects"
    if args_dirs:
        out = []
        for a in args_dirs:
            p = (root / a) if not Path(a).is_absolute() else Path(a)
            # allow PROJ-NNN prefix match
            if not p.is_dir():
                hits = sorted(root.glob(f"{a}*"))
                if hits:
                    p = hits[0]
            if p.is_dir():
                out.append(p)
        return out
    return sorted(p for p in root.iterdir()
                  if p.is_dir() and (p / "paper" / "source").is_dir())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("projects", nargs="*", help="PROJ-NNN dirs (default: all)")
    ap.add_argument("--min-pt", type=float, default=20.0,
                    help="Ignore overflows smaller than this (default 20pt).")
    ap.add_argument("--compile", action="store_true",
                    help="Compile any paper missing a log before auditing.")
    ap.add_argument("--top", type=int, default=15, help="How many worst to list.")
    args = ap.parse_args(argv)

    per_cat: dict[str, int] = defaultdict(int)
    per_cat_pt: dict[str, float] = defaultdict(float)
    per_paper: dict[str, dict[str, int]] = {}
    worst: list[tuple[float, str, str, str]] = []
    n_logs = 0

    for proj in _projects(args.projects):
        wrapper = proj / "paper" / "source" / "main-llmxive.tex"
        log = proj / "paper" / "pdf" / "main-llmxive.log"
        if args.compile and not log.is_file():
            subprocess.run([sys.executable, str(REPO / "scripts" / "compile_paper.py"),
                            str(proj)], capture_output=True, text=True)
        if not (log.is_file() and wrapper.is_file()):
            continue
        n_logs += 1
        wlines = wrapper.read_text(encoding="utf-8", errors="replace").splitlines()
        logtext = log.read_text(encoding="utf-8", errors="replace")
        cats: dict[str, int] = defaultdict(int)
        for m in OVERFULL_RE.finditer(logtext):
            kind, pt = m.group(1), float(m.group(2))
            if pt < args.min_pt:
                continue
            a = int(m.group(3)) if m.group(3) else 0
            b = int(m.group(4)) if m.group(4) else a
            cat = _classify(wlines, a, b, kind)
            cats[cat] += 1
            per_cat[cat] += 1
            per_cat_pt[cat] += pt
            snip = wlines[a - 1][:70] if 0 < a <= len(wlines) else ""
            worst.append((pt, proj.name.split("-")[0] + "-" + proj.name.split("-")[1],
                          cat, snip))
        if cats:
            per_paper[proj.name.split("-")[0] + "-" + proj.name.split("-")[1]] = dict(cats)

    print(f"Audited {n_logs} compiled paper log(s); overflows >= {args.min_pt:.0f}pt\n")
    print("BY CATEGORY (count, total pt):")
    if not per_cat:
        print("  (none)")
    for cat in sorted(per_cat, key=lambda c: -per_cat_pt[c]):
        print(f"  {cat:22s} count={per_cat[cat]:3d}  total={per_cat_pt[cat]:9.0f}pt")
    print("\nPER PAPER:")
    for proj in sorted(per_paper):
        print(f"  {proj}: " + ", ".join(f"{k}={v}" for k, v in sorted(per_paper[proj].items())))
    print(f"\nTOP {args.top} WORST:")
    for pt, proj, cat, snip in sorted(worst, reverse=True)[:args.top]:
        print(f"  {pt:8.0f}pt  {proj:10s} [{cat}]  {snip!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
