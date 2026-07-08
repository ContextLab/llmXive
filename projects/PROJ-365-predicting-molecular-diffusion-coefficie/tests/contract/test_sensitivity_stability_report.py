"""
Contract test for the sensitivity analysis summary report.

This test verifies that the generated
``artifacts/reports/sensitivity_summary.md`` file contains:

1. A clear stability statement (e.g., "Stability: stable" or "Stability: unstable").
2. At least one reported Pearson ``r`` value (or similar correlation metric).

The test is deliberately tolerant of minor formatting differences by using
regular expressions to locate the required information.
"""

import re
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def summary_path() -> Path:
    """
    Resolve the absolute path to the generated sensitivity summary markdown file.
    The file is expected to live at:
    ``artifacts/reports/sensitivity_summary.md`` relative to the repository root.
    """
    # ``__file__`` points to the test file inside ``tests/contract``.
    # Navigate up two levels to the repository root, then down to the artifact.
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "artifacts" / "reports" / "sensitivity_summary.md"
    return path


def test_sensitivity_summary_exists(summary_path: Path) -> None:
    """The summary markdown file must exist."""
    assert summary_path.is_file(), f"Missing summary report at {summary_path}"


def test_sensitivity_summary_contains_stability_statement(summary_path: Path) -> None:
    """
    The report must contain a stability statement.
    Acceptable forms include (case‑insensitive):

    - ``Stability: stable``
    - ``Stability = stable``
    - ``Stability: unstable``

    The test fails if no such line is found.
    """
    content = summary_path.read_text(encoding="utf-8")
    stability_pattern = re.compile(
        r"stability\s*[:=]\s*(stable|unstable)", re.IGNORECASE
    )
    match = stability_pattern.search(content)
    assert (
        match is not None
    ), "Stability statement not found in sensitivity_summary.md"


def test_sensitivity_summary_contains_r_values(summary_path: Path) -> None:
    """
    The report should list at least one Pearson ``r`` value (or any correlation
    metric that looks like a floating‑point number between -1 and 1).

    The test first looks for explicit ``r = <value>`` patterns; if none are
    found, it falls back to scanning for any floating‑point numbers within the
    valid correlation range.
    """
    content = summary_path.read_text(encoding="utf-8")

    # 1. Explicit ``r = <number>`` occurrences
    explicit_r = re.findall(r"r\s*[:=]\s*([-+]?\d*\.\d+)", content, flags=re.IGNORECASE)

    # 2. If no explicit matches, look for any float within [-1, 1]
    if not explicit_r:
        # Find all numbers that look like floats
        all_floats = re.findall(r"([-+]?\d*\.\d+)", content)
        # Keep only those that are within the correlation bounds
        explicit_r = [
            val for val in all_floats if -1.0 <= float(val) <= 1.0
        ]

    assert (
        explicit_r
    ), "No Pearson r values found in sensitivity_summary.md"
    # Optional sanity check: ensure values are in the valid range
    for val in explicit_r:
        r = float(val)
        assert -1.0 <= r <= 1.0, f"Found r value out of range: {r}"