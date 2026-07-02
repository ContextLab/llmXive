"""Unit test for the power‑limitation flag generation.

The test runs ``code/check_power_limitation.py``'s ``main`` function,
then verifies that the markdown report exists at the required location
and that it contains the appropriate flag when the computed power is
below the 0.70 threshold.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

# Import the script under test.
from check_power_limitation import main as generate_report

@pytest.fixture(autouse=True)
def cleanup_report():
    """Remove the report file before and after each test to ensure isolation."""
    report_path = Path(
        "projects/PROJ-586-social-memory-networks-modeling-collecti/results"
        "/power_analysis_report.md"
    )
    # Ensure a clean state.
    if report_path.is_file():
        report_path.unlink()
    yield
    # Clean up after the test.
    if report_path.is_file():
        report_path.unlink()

def test_report_is_created_and_contains_flag():
    """Run the generator and check for correct content."""
    generate_report()
    report_path = Path(
        "projects/PROJ-586-social-memory-networks-modeling-collecti/results"
        "/power_analysis_report.md"
    )
    assert report_path.is_file(), "Report markdown file was not created."

    content = report_path.read_text(encoding="utf-8")
    # The report must always contain the header and the estimated power line.
    assert "Power Analysis Report" in content
    assert "Estimated Power:" in content

    # Extract the numeric power value.
    import re

    match = re.search(r"Estimated Power:\\s*([0-9]*\\.?[0-9]+)", content)
    assert match, "Could not parse estimated power from report."
    power = float(match.group(1))

    # If the power is below the threshold, the flag must be present.
    if power < 0.70:
        assert "**Flag:** Power limitation" in content
    else:
        # Ensure we do not incorrectly flag high power.
        assert "**Flag:** Power limitation" not in content

# The test is deliberately simple and does not mock the underlying power
# analysis; it runs the real computation to guarantee that the report is
# based on genuine data rather than fabricated numbers.