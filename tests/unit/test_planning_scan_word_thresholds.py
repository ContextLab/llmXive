"""A threshold the project CHOSE stays concrete however it is worded.

Canary 9 (2026-10-11) spent four steps at the specification stage on one
disagreement. The idea fixes two reporting thresholds ("the scale at which
relative discrepancy first falls below 1% and 0.1%"). The spec stated them
three ways; the deterministic strip kept ``< 1% and < 0.1%`` and deferred the
same two values where they followed "below" or "fixed at". The panel flagged
the contradiction, the reviser restored the numbers, and the strip removed
them again on the next render -- three kickbacks, the same concern each time.
"""

from __future__ import annotations

import pytest

from llmxive.claims.planning_scan import (
    DEFERRED_MARKER,
    is_design_target,
    strip_empirical_values,
)

# The spec's own sentences, with the values the reviser kept restoring.
_CHOSEN = [
    "- **FR-007**: report the scale N at which relative discrepancy first falls below 1% and below 0.1%.",
    "- **Threshold not reached**: if relative discrepancy never falls below 1% (or below 0.1%) "
    "by N = 10^6 for some p, the output must state so.",
    "- The reporting thresholds for relative discrepancy are fixed at 1% and 0.1% respectively; "
    "these are descriptive reporting conventions derived from the source idea.",
    "- **SC-004**: the scale at which relative discrepancy first falls below 1% and 0.1% is reported.",
    "- Flag a prime when the discrepancy rises above 5%.",
    "- The cutoff is set to 2.5% for every scale.",
    "- Retries are capped at 3%, 5%, or 10% of the batch, set at 3% by default.",
]


@pytest.mark.parametrize("line", _CHOSEN)
def test_chosen_threshold_is_kept(line: str) -> None:
    assert strip_empirical_values(line) == line


@pytest.mark.parametrize("line", _CHOSEN[:6])
def test_chosen_threshold_is_a_design_target_for_the_claim_pass(line: str) -> None:
    assert is_design_target(line)


@pytest.mark.parametrize("line,expected", [
    # A bare assertion about the world is still deferred, and so is the one
    # joined to it: "and" carries the status of what it follows, either way.
    ("- 95% of records and 3% of rows are complete.",
     f"- {DEFERRED_MARKER} of records and {DEFERRED_MARKER} of rows are complete."),
    ("- The corpus holds approximately 27,635 papers and 1,204 preprints.",
     f"- The corpus holds {DEFERRED_MARKER} papers and {DEFERRED_MARKER} preprints."),
    # A chosen threshold does not shelter an unrelated measurement later on.
    ("- Flag a prime above 5%; in the pilot 12% of primes were flagged.",
     f"- Flag a prime above 5%; in the pilot {DEFERRED_MARKER} of primes were flagged."),
])
def test_measured_values_are_still_deferred(line: str, expected: str) -> None:
    assert strip_empirical_values(line) == expected


def test_kept_lines_are_stable_across_renders() -> None:
    text = "\n".join(_CHOSEN)
    once = strip_empirical_values(text)
    assert strip_empirical_values(once) == once == text
