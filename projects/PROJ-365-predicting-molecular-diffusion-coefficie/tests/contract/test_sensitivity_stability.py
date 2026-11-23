"""
Contract test for the sensitivity analysis summary report.

This test verifies that the generated ``sensitivity_summary.md`` report
contains:
  1. A stability statement (the word ``stable`` or ``unstable``).
  2. At least one recorded Pearson ``r`` value (a floating‑point number).

The test is deliberately lightweight and does not depend on the internal
implementation of the sensitivity analysis; it only checks the existence
and basic content of the report file.
"""

import re
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def summary_path() -> Path:
    """
    Returns the path to the sensitivity summary markdown file.
    """
    return Path("artifacts/reports/sensitivity_summary.md")


def test_summary_report_exists(summary_path: Path) -> None:
    """The summary report file must exist."""
    assert summary_path.is_file(), f"Missing report: {summary_path}"


def test_stability_statement_present(summary_path: Path) -> None:
    """
    The report must contain a stability statement indicating either
    ``stable`` or ``unstable``.
    """
    content = summary_path.read_text(encoding="utf-8").lower()
    # Look for a line that mentions stability; allow flexible wording.
    stability_match = re.search(r"stability[:\\s]*([a-z]+)", content)
    assert stability_match is not None, "Stability statement not found in report."
    status = stability_match.group(1)
    assert status in {"stable", "unstable"}, (
        f"Unexpected stability status '{status}'. Expected 'stable' or 'unstable'."
    )


def test_pearson_r_values_recorded(summary_path: Path) -> None:
    """
    The report must contain at least one Pearson correlation coefficient
    (floating‑point number) associated with an ``r`` value.
    """
    content = summary_path.read_text(encoding="utf-8")
    # Find patterns like ``r = 0.85`` or ``r:0.85`` etc.
    r_values = re.findall(r"r\\s*[:=]\\s*[-+]?(?:\\d*\\.\\d+|\\d+)", content, flags=re.IGNORECASE)
    assert r_values, "No Pearson r values found in the sensitivity summary report."
    # Optionally, ensure they can be parsed as floats.
    for r_str in r_values:
        # Extract the numeric part.
        num_match = re.search(r"[-+]?(?:\\d*\\.\\d+|\\d+)", r_str)
        assert num_match, f"Failed to extract numeric value from '{r_str}'."
        try:
            float(num_match.group(0))
        except ValueError as exc:
            raise AssertionError(f"Invalid float value in r entry '{r_str}': {exc}") from exc