"""Differential clean-vs-injected calibration harness (spec 015 T065).

The harness runs a panel against two inputs — a clean artifact + an
artifact mutated by a known flaw injector — and diffs the verdicts:

- **Missed injection** (false negative): the injected artifact passed
  with no flagged concern matching the injector's ``expected_lens``.
  This is the panel's calibration MISS.
- **Extra findings** (over-flagging surface): the clean artifact ALSO
  surfaced concerns. Each one is logged for human adjudication — it
  may be a real flaw the panel correctly noticed, or a false positive.
- **Caught injection** (true positive): the injected artifact yielded
  a concern matching the expected_lens.

The harness produces a markdown adjudication report with one section
per injection run. The maintainer reviews the report, marks each
"extra finding" as legitimate / spurious, and adjusts panel prompts
accordingly. See FR-046.

This module is the pure data-processing layer — it does NOT itself run
the engine or call any LLM. The calibration driver (T068) is
responsible for invoking the engine on each clean+injected pair and
passing the resulting ConvergenceResult objects to ``adjudicate``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from llmxive.convergence.types import Concern, ConvergenceResult

from .injectors import Injection


@dataclass(frozen=True)
class _PanelOutcome:
    """A single panel run's result, reduced to what the adjudicator needs."""

    converged: bool
    flagged_lenses: tuple[str, ...]
    concerns: tuple[Concern, ...]


def _summarize(result: ConvergenceResult) -> _PanelOutcome:
    """Reduce a ConvergenceResult to the lens-set + concern list."""
    lenses = tuple(sorted({c.reviewer for c in result.concern_history}))
    return _PanelOutcome(
        converged=result.converged,
        flagged_lenses=lenses,
        concerns=tuple(result.concern_history),
    )


@dataclass
class CalibrationRun:
    """One pairing of an injector + the two panel runs it produced."""

    injector_name: str
    injection: Injection
    clean_result: ConvergenceResult
    injected_result: ConvergenceResult

    @property
    def expected_lens(self) -> str:
        return self.injection.expected_lens

    @property
    def caught(self) -> bool:
        """True iff the injected run flagged the expected lens."""
        return self.expected_lens in _summarize(self.injected_result).flagged_lenses

    @property
    def extra_findings_on_clean(self) -> list[Concern]:
        """Concerns the panel surfaced on the CLEAN artifact (these are
        candidates for human adjudication — may be true positives the
        panel correctly noticed in a deliberately-clean sample, or false
        positives the prompts need to address)."""
        return list(_summarize(self.clean_result).concerns)


@dataclass
class AdjudicationReport:
    """Aggregate report across multiple CalibrationRuns."""

    runs: list[CalibrationRun] = field(default_factory=list)

    @property
    def caught_count(self) -> int:
        return sum(1 for r in self.runs if r.caught)

    @property
    def missed_count(self) -> int:
        return sum(1 for r in self.runs if not r.caught)

    @property
    def total_extra_findings(self) -> int:
        return sum(len(r.extra_findings_on_clean) for r in self.runs)

    def to_markdown(self, *, domain: str = "(unspecified)") -> str:
        """Render the report as a maintainer-readable markdown document.

        Sensitivity tuning per the design doc (FR-046) is DIFFERENTIAL +
        manual: there is no fixed over-flag percentage threshold. The
        report calls out every clean-side concern + every miss so the
        maintainer can decide which prompt changes to make.
        """
        lines: list[str] = []
        lines.append(f"# Calibration adjudication — domain: {domain}")
        lines.append("")
        lines.append(
            f"**Summary**: {self.caught_count} of {len(self.runs)} "
            f"injections caught · {self.missed_count} missed · "
            f"{self.total_extra_findings} extra finding(s) on clean "
            f"artifacts (each flagged for manual adjudication)."
        )
        lines.append("")
        lines.append(
            "Per design SSoT (FR-046): adjustment is DIFFERENTIAL + "
            "manual. There is no fixed over-flag % threshold; the "
            "maintainer reviews each extra finding below and marks "
            "it 'legitimate' (panel correctly noticed real flaw in a "
            "supposedly-clean sample → fix the sample) or 'spurious' "
            "(prompt over-strict → adjust the prompt)."
        )
        lines.append("")
        for i, run in enumerate(self.runs, start=1):
            lines.append(f"## {i}. Injector: `{run.injector_name}`")
            lines.append("")
            lines.append(f"- **Expected lens**: `{run.expected_lens}`")
            lines.append(f"- **Description**: {run.injection.description}")
            status = "✅ CAUGHT" if run.caught else "❌ MISSED (false negative)"
            lines.append(f"- **Status**: {status}")
            injected_lenses = _summarize(run.injected_result).flagged_lenses
            lines.append(
                f"- **Lenses flagged on injected**: "
                f"{', '.join(injected_lenses) if injected_lenses else '(none)'}"
            )
            lines.append("")
            extras = run.extra_findings_on_clean
            if extras:
                lines.append(
                    f"### Extra findings on the CLEAN artifact "
                    f"({len(extras)}) — needs adjudication"
                )
                lines.append("")
                for c in extras:
                    lines.append(
                        f"- `{c.reviewer}` [{c.severity.value}] "
                        f"`{c.location or '(unstated)'}` — {c.text}"
                    )
                lines.append("")
                lines.append("**Adjudication** (maintainer to fill in):")
                lines.append("")
                for j, _c in enumerate(extras, start=1):
                    lines.append(f"- [ ] {i}.{j}: legitimate / spurious — reasoning:")
                lines.append("")
            else:
                lines.append("Clean artifact surfaced no concerns. ✅")
                lines.append("")
        return "\n".join(lines)


def adjudicate(
    runs: list[CalibrationRun], *, domain: str = "(unspecified)"
) -> AdjudicationReport:
    """Build an :class:`AdjudicationReport` from a list of calibration
    runs. Pure function — no I/O, no LLM calls. Drivers call this AFTER
    they've run the engine on each (clean, injected) pair."""
    report = AdjudicationReport(runs=list(runs))
    # No further computation needed at construction time — the
    # properties + to_markdown() are lazy.
    _ = domain  # consumed by to_markdown only
    return report


__all__ = [
    "AdjudicationReport",
    "CalibrationRun",
    "adjudicate",
]
