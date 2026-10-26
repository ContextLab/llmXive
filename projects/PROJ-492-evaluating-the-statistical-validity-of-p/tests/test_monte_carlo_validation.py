"""
Integration test for the Monte‑Carlo validation script (T004).

The test simply imports the ``run_monte_carlo_validation`` function,
executes it with a temporary output path, and asserts that:
  * the overall suite passes,
  * the JSON file is created,
  * each individual test reports ``passed == True``.

This ensures that the script runs end‑to‑end without fabricating data
and that the output adheres to the naming convention required by the
specification.
"""

import json
from pathlib import Path

import pytest

# Import the function from the module under test
from code.src.audit.monte_carlo_validation import run_monte_carlo_validation


@pytest.fixture
def temp_output(tmp_path: Path) -> Path:
    """Create a temporary ``output`` directory for the JSON report."""
    out_dir = tmp_path / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / "monte_carlo_validation_report.json"


def test_monte_carlo_validation_suite(temp_output: Path):
    """Run the suite and verify the JSON report."""
    results = run_monte_carlo_validation(output_path=temp_output)

    # The suite must report overall success
    assert results["summary"]["overall_passed"] is True
    assert results["summary"]["failed"] == 0
    assert results["summary"]["passed"] == results["summary"]["total_tests"]

    # The output file must exist and be valid JSON
    assert temp_output.is_file()
    with temp_output.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # The file content should match the returned results dict
    assert data == results
    
    # Every individual test must have passed
    for test in data["tests"]:
        assert test["passed"] is True
        assert test["absolute_difference"] <= 0.005

# Ensure the script’s ``main`` returns a zero exit code when invoked directly
def test_main_returns_zero(monkeypatch, tmp_path):
    """Patch sys.argv to invoke the module as a script."""
    from code.src.audit import monte_carlo_validation
    import sys

    # Replace the default output path with a temporary location
    temp_file = tmp_path / "output" / "monte_carlo_validation_report.json"
    temp_file.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        monte_carlo_validation,
        "Path",
        lambda *args, **kwargs: temp_file,  # type: ignore
    )

    # Run main and capture the exit code
    exit_code = monte_carlo_validation.main()
    assert exit_code == 0
    assert temp_file.is_file()