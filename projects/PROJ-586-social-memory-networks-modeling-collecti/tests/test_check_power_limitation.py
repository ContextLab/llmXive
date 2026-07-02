"""Tests for the ``check_power_limitation`` script.

The tests verify that the script creates the markdown file at the correct
location and that the *Power limitation* flag is added only when the
estimated power is below the 0.70 threshold.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest

# Import the script's main function via its module path.
from check_power_limitation import main as cli_main

# Helper to locate the default report path used by the script.
DEFAULT_REPORT = Path(
    "projects/PROJ-586-social-memory-networks-modeling-collecti/results/power_analysis_report.md"
).resolve()


@pytest.fixture
def temp_dir(tmp_path: Path):
    """Create an isolated temporary directory for each test."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)


def test_report_created_with_flag_when_power_low(monkeypatch, temp_dir):
    """Simulate a low‑power result (<0.70) and ensure the flag appears."""
    # Stub ``run_power_analysis`` to return a simple namespace with low power.
    class DummyResult:
        estimated_power = 0.55

    monkeypatch.setattr(
        "analysis.power.run_power_analysis",
        lambda: DummyResult(),
    )
    # Run the CLI with the default arguments.
    exit_code = cli_main([])
    assert exit_code == 0

    # The report file must exist at the required location.
    assert DEFAULT_REPORT.is_file()

    content = DEFAULT_REPORT.read_text(encoding="utf-8")
    assert "Estimated Power: 0.550" in content
    assert "Power limitation" in content


def test_report_without_flag_when_power_high(monkeypatch, temp_dir):
    """Simulate a high‑power result (≥0.70) and ensure no flag is added."""
    class DummyResult:
        estimated_power = 0.85

    monkeypatch.setattr(
        "analysis.power.run_power_analysis",
        lambda: DummyResult(),
    )
    exit_code = cli_main([])
    assert exit_code == 0
    assert DEFAULT_REPORT.is_file()
    content = DEFAULT_REPORT.read_text(encoding="utf-8")
    assert "Estimated Power: 0.850" in content
    assert "Power limitation" not in content


def test_fallback_to_csv_when_analysis_fails(monkeypatch, temp_dir):
    """If ``run_power_analysis`` raises, the script should read the CSV fallback."""
    # Force the analysis function to raise an exception.
    monkeypatch.setattr(
        "analysis.power.run_power_analysis",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    # Create a CSV file with a low power value.
    csv_path = Path("data/power_analysis_results.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text(
        "estimated_power\\n0.60\\n",
        encoding="utf-8",
    )
    exit_code = cli_main([])
    assert exit_code == 0
    assert DEFAULT_REPORT.is_file()
    content = DEFAULT_REPORT.read_text(encoding="utf-8")
    assert "Estimated Power: 0.600" in content
    assert "Power limitation" in content