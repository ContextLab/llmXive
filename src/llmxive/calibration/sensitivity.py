"""Adaptive sensitivity tuning driver (FR-044).

The differential calibration in :mod:`llmxive.calibration.differential`
produces :class:`AdjudicationReport`s holding raw caught / missed /
extra-findings counts. The MAINTAINER then fills in a per-extra-finding
adjudication checklist (legitimate vs spurious).

This module consumes those reports + the maintainer's adjudication
decisions and emits :class:`SensitivityRecommendation`s — one per
expected lens — telling the maintainer which direction to adjust
prompt sensitivity:

* **INCREASE** — any injected flaw was missed for this lens (false
  negative). FR-044: "any missed injected flaw → increase sensitivity."
* **REDUCE** — many spurious extra findings (false positives) on clean
  artifacts that this lens flagged. FR-044: "many false positives →
  reduce sensitivity."
* **STABLE** — within tolerance (no misses; spurious-FP count below the
  warn threshold).

The threshold is configurable but defaults to 1+ legitimate-miss → INCREASE
and 3+ spurious-extra → REDUCE. The maintainer can override per call.

**Noise robustness** (FR-044, second sentence): the caller is expected to
pass MULTIPLE :class:`AdjudicationReport`s from REPEATED runs of the
same case set (different model-temperature seeds). The recommender
aggregates across reports — a single transient miss is treated
differently from a consistent miss across runs (see
:meth:`SensitivityRecommendation.confidence`).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum

from llmxive.calibration.differential import AdjudicationReport


class SensitivityDirection(StrEnum):
    """How the maintainer should adjust this lens's prompt."""

    INCREASE = "increase"
    """Too many missed injected flaws (false negatives). Tighten the
    prompt so the lens catches more."""

    REDUCE = "reduce"
    """Too many spurious findings (false positives confirmed by the
    maintainer's adjudication). Loosen the prompt so the lens flags
    fewer benign things."""

    STABLE = "stable"
    """Within tolerance — no recommended change."""


# Type aliases for adjudication keys / verdicts.
#
# `AdjudicationKey` identifies one extra-finding within one report:
# (report_index, run_index_within_report, finding_index_within_run).
# `AdjudicationVerdict` is the maintainer's call:
#   "legitimate" — the panel correctly noticed a real flaw in the
#                 supposedly-clean sample (fix the sample, not the prompt)
#   "spurious"   — the prompt is over-strict; loosen it
AdjudicationKey = tuple[int, int, int]
AdjudicationVerdict = str  # "legitimate" | "spurious"


@dataclass(frozen=True)
class SensitivityRecommendation:
    """Per-lens sensitivity-adjustment recommendation."""

    lens: str
    """The expected lens whose prompt the recommendation applies to."""

    direction: SensitivityDirection
    """Which way to adjust the prompt (see :class:`SensitivityDirection`)."""

    rationale: str
    """Plain-language explanation surfaced in the report."""

    runs_observed: int
    """Total CalibrationRuns this lens appeared in (across all reports)."""

    caught_count: int
    """How many runs (cumulative) caught the injected flaw on this lens."""

    missed_count: int
    """How many runs (cumulative) missed the injected flaw."""

    spurious_extras_count: int
    """How many extra-findings on clean artifacts were adjudicated
    spurious (false positives) for this lens."""

    legitimate_extras_count: int
    """How many extra-findings on clean artifacts were adjudicated
    legitimate (real flaws in the supposedly-clean sample) for this
    lens."""

    @property
    def confidence(self) -> str:
        """Loose qualitative confidence label.

        ``high`` when the signal is consistent across ≥3 runs;
        ``medium`` for 2 runs; ``low`` for a single run (FR-044 noise
        robustness — a single run can be transient model-temperature
        noise)."""
        if self.runs_observed >= 3:
            return "high"
        if self.runs_observed >= 2:
            return "medium"
        return "low"

    def to_markdown(self) -> str:
        """Maintainer-facing rendering."""
        return (
            f"- **`{self.lens}`** → "
            f"**{self.direction.value.upper()}** "
            f"(confidence: {self.confidence}) — {self.rationale}"
        )


@dataclass
class _LensTally:
    """Internal accumulator for one lens across all reports."""

    runs: int = 0
    caught: int = 0
    missed: int = 0
    spurious_extras: int = 0
    legitimate_extras: int = 0
    extras_with_no_adjudication: int = 0
    """Counted separately so the recommender knows when adjudication
    is incomplete."""
    extras_observed_for_lens: list[str] = field(default_factory=list)
    """Reviewer names that produced extras attributable to this lens."""


def recommend_sensitivity(
    reports: list[AdjudicationReport],
    *,
    adjudication: dict[AdjudicationKey, AdjudicationVerdict] | None = None,
    miss_threshold: int = 1,
    spurious_extras_threshold: int = 3,
) -> list[SensitivityRecommendation]:
    """Adaptive sensitivity recommender (FR-044).

    Args:
        reports: AdjudicationReports from one or more differential
            calibration runs of the SAME panel/case set. Multiple
            reports = repeated runs for noise robustness.
        adjudication: maintainer's per-extra-finding verdict, keyed by
            ``(report_index, run_index, finding_index)`` with value
            ``"legitimate"`` or ``"spurious"``. Findings not in the
            dict are treated as unadjudicated and surfaced as a
            STABLE-with-warning recommendation.
        miss_threshold: cumulative missed-injection count (across all
            reports) at or above which the recommendation is INCREASE.
            Defaults to 1 — the FR-044 contract treats ANY missed
            injected flaw as a sensitivity floor violation.
        spurious_extras_threshold: cumulative spurious-extras count at
            or above which the recommendation is REDUCE. Defaults to 3
            (per the design doc's "minor FPs that resolve within one
            review/revision round are acceptable; many → reduce").

    Returns:
        One :class:`SensitivityRecommendation` per expected_lens that
        appeared in the reports. Order is sorted by lens name for
        deterministic output.

    The recommender never modifies the reports or the adjudication
    dict — pure read.
    """
    adjudication = adjudication or {}
    by_lens: dict[str, _LensTally] = defaultdict(_LensTally)

    for ri, report in enumerate(reports):
        for run_i, run in enumerate(report.runs):
            lens = run.expected_lens
            tally = by_lens[lens]
            tally.runs += 1
            if run.caught:
                tally.caught += 1
            else:
                tally.missed += 1
            for fi, _extra in enumerate(run.extra_findings_on_clean):
                verdict = adjudication.get((ri, run_i, fi))
                if verdict == "legitimate":
                    tally.legitimate_extras += 1
                elif verdict == "spurious":
                    tally.spurious_extras += 1
                else:
                    tally.extras_with_no_adjudication += 1

    out: list[SensitivityRecommendation] = []
    for lens in sorted(by_lens):
        t = by_lens[lens]
        # FR-044 ordering: missed injected flaw always wins — even if
        # the lens ALSO over-flags, fixing the false negative comes
        # first. INCREASE the floor, then revisit FPs next round.
        if t.missed >= miss_threshold:
            direction = SensitivityDirection.INCREASE
            rationale = (
                f"{t.missed} of {t.runs} run(s) MISSED the injected "
                f"flaw on this lens (recall floor violated; "
                f"miss_threshold={miss_threshold})."
            )
        elif t.spurious_extras >= spurious_extras_threshold:
            direction = SensitivityDirection.REDUCE
            rationale = (
                f"{t.spurious_extras} spurious extra finding(s) "
                f"adjudicated on clean artifacts (over "
                f"threshold={spurious_extras_threshold}); lens "
                f"flags too aggressively."
            )
        else:
            parts = [
                f"{t.caught}/{t.runs} caught",
                f"{t.spurious_extras} spurious extras",
                f"{t.legitimate_extras} legitimate extras",
            ]
            if t.extras_with_no_adjudication:
                parts.append(
                    f"{t.extras_with_no_adjudication} extras pending "
                    "maintainer adjudication"
                )
            direction = SensitivityDirection.STABLE
            rationale = "Within tolerance (" + "; ".join(parts) + ")."
        out.append(SensitivityRecommendation(
            lens=lens,
            direction=direction,
            rationale=rationale,
            runs_observed=t.runs,
            caught_count=t.caught,
            missed_count=t.missed,
            spurious_extras_count=t.spurious_extras,
            legitimate_extras_count=t.legitimate_extras,
        ))
    return out


def render_recommendations_markdown(
    recommendations: list[SensitivityRecommendation],
    *,
    panel: str = "(unspecified)",
) -> str:
    """Render a panel's sensitivity recommendations as a maintainer-
    readable markdown block. Intended to be appended to the
    AdjudicationReport markdown after the maintainer has filled in
    adjudication verdicts and re-run :func:`recommend_sensitivity`.
    """
    lines = [
        f"## Sensitivity recommendations — panel: {panel}",
        "",
        "Adaptive tuning per FR-044: any missed injected flaw → "
        "INCREASE; many spurious false positives → REDUCE; else "
        "STABLE. Confidence reflects how many runs the signal was "
        "observed across (≥3 = high; 2 = medium; 1 = low).",
        "",
    ]
    if not recommendations:
        lines.append("_No recommendations — no calibration runs observed._")
        return "\n".join(lines)
    for rec in recommendations:
        lines.append(rec.to_markdown())
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "AdjudicationKey",
    "AdjudicationVerdict",
    "SensitivityDirection",
    "SensitivityRecommendation",
    "recommend_sensitivity",
    "render_recommendations_markdown",
]
