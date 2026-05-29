#!/usr/bin/env python3
"""Driver for the FR-044 adaptive sensitivity recommender.

Reads one or more adjudicated calibration reports from disk, extracts
the maintainer's per-extra-finding adjudication verdicts from each
report's checklist, runs :func:`llmxive.calibration.sensitivity.
recommend_sensitivity`, and prints (or appends) the per-lens
recommendations.

The maintainer's workflow:

1. ``scripts/run_calibration.py`` produces an initial report under
   ``specs/015-pipeline-convergence-protocol/calibration/reports/<stage>__<timestamp>.md``.
   The report includes an adjudication checklist; every extra finding
   on a clean artifact is rendered as
   ``- [ ] {i}.{j}: legitimate / spurious — reasoning:``.
2. The maintainer fills the checklist in by REPLACING the leading
   ``- [ ]`` with either ``- [legitimate]`` or ``- [spurious]`` AND
   appending the reasoning after ``reasoning:``.
3. The maintainer runs this script (passing one or more adjudicated
   report files); the recommendations are printed AND optionally
   appended to each report.

Usage::

    python scripts/recommend_sensitivity.py \
        specs/015-pipeline-convergence-protocol/calibration/reports/spec__*.md

    python scripts/recommend_sensitivity.py --append-to-reports \
        specs/015-pipeline-convergence-protocol/calibration/reports/spec__2026-05-28T*.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# The runner builds AdjudicationReports in-memory; this driver re-builds
# them from the maintainer-adjudicated markdown so multiple reports
# (different seeds = noise robustness) can be aggregated. We parse the
# minimal subset we need: (lens, caught/missed/extra) per run and the
# checklist verdicts per extra.

_INJECTOR_HEADER_RE = re.compile(r"^##\s+\d+\.\s+Injector:\s+`([^`]+)`", re.MULTILINE)
_LENS_RE = re.compile(r"^-\s+\*\*Expected lens\*\*:\s+`([^`]+)`", re.MULTILINE)
_STATUS_CAUGHT_RE = re.compile(r"^-\s+\*\*Status\*\*:\s+✅\s+CAUGHT", re.MULTILINE)
_STATUS_MISSED_RE = re.compile(r"^-\s+\*\*Status\*\*:\s+❌\s+MISSED", re.MULTILINE)
# Runner-version tag (FR-044 noise robustness). Written by
# AdjudicationReport.to_markdown(runner_version=...) as an HTML comment
# on line 2 of the report. Returns None if the report predates the
# tag (legacy reports stay un-versioned).
_VERSION_RE = re.compile(
    r"^<!--\s*runner_version:\s*(\S+)\s*-->\s*$", re.MULTILINE,
)
# Adjudicated line examples we accept:
#   - [legitimate] 1.2: ... — reasoning: ...
#   - [spurious]   3.1: ... — reasoning: ...
# We also accept the unchecked form `- [ ] ...` as "not yet adjudicated".
_ADJ_LINE_RE = re.compile(
    r"^-\s+\[(legitimate|spurious|\s)\]\s+(\d+)\.(\d+):", re.MULTILINE,
)


def _parse_runner_version(text: str) -> str | None:
    """Extract the runner-version tag from a report. Returns ``None``
    for legacy reports without the tag."""
    m = _VERSION_RE.search(text)
    return m.group(1) if m is not None else None


def _parse_one_report(text: str) -> tuple[list[dict], dict[tuple[int, int], str]]:
    """Parse one adjudicated report.

    Returns:
        (runs, adjudication) — ``runs`` is a list of one dict per
        injector entry; ``adjudication`` is a dict mapping
        ``(run_index, finding_index_within_run)`` → ``"legitimate"`` /
        ``"spurious"`` for those the maintainer adjudicated. Indices
        are 1-based to mirror the markdown checklist.
    """
    # Split into per-injector sections so we can pair lens + status.
    sections = re.split(r"^## ", text, flags=re.MULTILINE)
    runs: list[dict] = []
    for sec in sections[1:]:  # first section is the report header
        # Re-prefix `## ` for the regexes that anchor on ^##.
        body = "## " + sec
        lens_m = _LENS_RE.search(body)
        if not lens_m:
            continue
        caught = bool(_STATUS_CAUGHT_RE.search(body))
        missed = bool(_STATUS_MISSED_RE.search(body))
        # Extras-count: count of ``- [` lines whose `i.` matches this
        # entry's 1-based position (we'll do per-run lookup below).
        runs.append({
            "lens": lens_m.group(1),
            "caught": caught,
            "missed": missed,
        })

    adjudication: dict[tuple[int, int], str] = {}
    for m in _ADJ_LINE_RE.finditer(text):
        verdict = m.group(1).strip()
        i = int(m.group(2)) - 1  # markdown is 1-based; map to 0-based
        j = int(m.group(3)) - 1
        if verdict in ("legitimate", "spurious"):
            adjudication[(i, j)] = verdict
        # else: unadjudicated (the checklist is still empty)

    return runs, adjudication


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "reports", nargs="+", type=Path,
        help="One or more adjudicated calibration report markdown files. "
             "Multiple reports for the same panel = repeated runs for "
             "noise robustness (FR-044).",
    )
    p.add_argument(
        "--panel", default="(unspecified)",
        help="Panel label for the recommendation header.",
    )
    p.add_argument(
        "--append-to-reports", action="store_true",
        help="After computing recommendations, append the rendered "
             "markdown block to EACH input report file.",
    )
    p.add_argument(
        "--miss-threshold", type=int, default=1,
        help="Cumulative missed-injection count (across all reports) "
             "at or above which the recommendation is INCREASE.",
    )
    p.add_argument(
        "--spurious-threshold", type=int, default=3,
        help="Cumulative spurious-extras count at or above which the "
             "recommendation is REDUCE.",
    )
    p.add_argument(
        "--version-filter", default=None,
        help="FR-044 noise robustness: aggregate ONLY reports whose "
             "runner_version tag matches this value (typically a git "
             "short hash). Reports of unknown (untagged) version are "
             "EXCLUDED when this flag is active. Use 'latest' to "
             "auto-pick the most-common version across the inputs.",
    )
    args = p.parse_args(argv)

    # Build in-memory AdjudicationReports + a unified adjudication dict
    # whose keys are (report_index, run_index, finding_index) per the
    # sensitivity recommender's contract.
    from llmxive.calibration.differential import (
        AdjudicationReport,
        CalibrationRun,
    )
    from llmxive.calibration.injectors import Injection
    from llmxive.calibration.sensitivity import (
        recommend_sensitivity,
        render_recommendations_markdown,
    )
    from llmxive.convergence.types import (
        Concern,
        ConvergenceResult,
        Severity,
        Verdict,
    )

    reports: list[AdjudicationReport] = []
    report_versions: list[str | None] = []
    unified_adj: dict[tuple[int, int, int], str] = {}
    for ri, report_path in enumerate(args.reports):
        text = report_path.read_text(encoding="utf-8")
        report_versions.append(_parse_runner_version(text))
        parsed_runs, adjudication = _parse_one_report(text)
        runs: list[CalibrationRun] = []
        for run_idx, run_info in enumerate(parsed_runs):
            lens = run_info["lens"]
            # Synthesize the minimum ConvergenceResults the recommender
            # needs: the differential.CalibrationRun reads `caught` via
            # `injected_result`'s flagged lenses; clean extras are read
            # from `clean_result`'s concerns. We don't reconstruct the
            # exact concerns — we only need the lens-level shape.
            injected_concerns: list[Concern] = []
            injected_verdicts: list[Verdict] = []
            if run_info["caught"]:
                c = Concern(
                    id=f"INJ-{run_idx + 1:03d}", reviewer=lens,
                    severity=Severity.SCIENCE, artifact="x", location="", text="",
                )
                injected_concerns.append(c)
                injected_verdicts.append(
                    Verdict(concern_id=c.id, reviewer=lens, status="fail")
                )
            injected = ConvergenceResult(
                stage="clarified", converged=not run_info["caught"],
                rounds_used=1, concern_history=injected_concerns,
                verdict_history=injected_verdicts,
            )
            clean = ConvergenceResult(
                stage="clarified", converged=True, rounds_used=1,
            )
            runs.append(CalibrationRun(
                injector_name=f"entry-{run_idx + 1}",
                injection=Injection(
                    text="", expected_lens=lens, description="",
                    original="clarified",
                ),
                clean_result=clean,
                injected_result=injected,
            ))
        reports.append(AdjudicationReport(runs=runs))
        for (run_i, fi), verdict in adjudication.items():
            unified_adj[(ri, run_i, fi)] = verdict

    # Resolve --version-filter, including the "latest" auto-pick
    # convention (most-common runner_version across the input set;
    # ties broken by lexicographic order so the output is reproducible).
    version_filter: str | None = args.version_filter
    if version_filter == "latest":
        from collections import Counter
        known = [v for v in report_versions if v is not None]
        if not known:
            print(
                "[recommend-sensitivity] WARNING: --version-filter=latest "
                "supplied but NO reports carry a runner_version tag. "
                "Falling back to all-reports aggregation.",
                file=sys.stderr,
            )
            version_filter = None
        else:
            counter = Counter(known)
            # most_common(1) returns [(version, count)]; resolve ties
            # via lexicographic order on the version string.
            top_count = counter.most_common(1)[0][1]
            top_versions = sorted(v for v, c in counter.items() if c == top_count)
            version_filter = top_versions[0]
            print(
                f"[recommend-sensitivity] --version-filter=latest "
                f"resolved to {version_filter!r} "
                f"({counter[version_filter]} of {len(reports)} reports).",
                file=sys.stderr,
            )

    recs = recommend_sensitivity(
        reports,
        adjudication=unified_adj,
        miss_threshold=args.miss_threshold,
        spurious_extras_threshold=args.spurious_threshold,
        version_filter=version_filter,
        report_versions=report_versions if version_filter is not None else None,
    )
    rendered = render_recommendations_markdown(recs, panel=args.panel)

    print(rendered)

    if args.append_to_reports:
        for report_path in args.reports:
            with report_path.open("a", encoding="utf-8") as f:
                f.write("\n\n---\n\n")
                f.write(rendered)
            print(f"[recommend-sensitivity] appended → {report_path}",
                  file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
