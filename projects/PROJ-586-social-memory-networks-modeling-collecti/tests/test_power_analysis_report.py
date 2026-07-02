"""Test that the power analysis report is generated at the correct location
and that the ``Power limitation`` flag appears when appropriate.

The test runs the ``generate_power_report`` script with a mocked power
analysis result to avoid expensive computation. It then checks that:
* The markdown file exists at the required path.
* The file contains the estimated power value.
* If the mocked power is below 0.70, the flag line is present.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest import mock

# Import the script as a module so we can call its ``main`` function.
script_path = Path(__file__).parents[2] / "code" / "generate_power_report.py"
spec = importlib.util.spec_from_file_location("generate_power_report", script_path)
assert spec and spec.loader, "Failed to load generate_power_report module"
generate_power_report = importlib.util.module_from_spec(spec)
sys.modules["generate_power_report"] = generate_power_report
spec.loader.exec_module(generate_power_report)  # type: ignore[arg-type]

# Helper to locate the expected output file.
def expected_report_path() -> Path:
    return (
        Path(__file__).parents[4]
        / "projects"
        / "PROJ-586-social-memory-networks-modeling-collecti"
        / "results"
        / "power_analysis_report.md"
    )

def run_and_check(mock_power: float, expect_flag: bool) -> None:
    """Run the script with a mocked ``run_power_analysis`` result."""
    # Ensure a clean state before each run.
    report_path = expected_report_path()
    if report_path.exists():
        report_path.unlink()

    # Mock the ``run_power_analysis`` function to return a deterministic result.
    mock_result = mock.Mock()
    mock_result.estimated_power = mock_power

    with mock.patch.object(
        generate_power_report,
        "run_power_analysis",
        return_value=mock_result,
    ):
        # ``argv`` is ``None`` so the script uses its defaults.
        exit_code = generate_power_report.main([])

    assert exit_code == 0, "Script did not exit cleanly"
    assert report_path.is_file(), f"Report not created at {report_path}"

    content = report_path.read_text(encoding="utf-8")
    assert f"Estimated Power:** {mock_power:.3f}" in content

    flag_line = "Power limitation" in content
    assert flag_line is expect_flag, (
        f"Flag presence mismatch: expected {expect_flag}, got {flag_line}"
    )

def test_report_with_high_power() -> None:
    """When power >= 0.70 the flag must NOT appear."""
    run_and_check(mock_power=0.85, expect_flag=False)

def test_report_with_low_power() -> None:
    """When power < 0.70 the flag must appear."""
    run_and_check(mock_power=0.55, expect_flag=True)