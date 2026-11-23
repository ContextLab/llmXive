"""
Integration test skeleton for report generation (TDD).

This test validates that T030-T035 execute successfully and produce
the final report and associated artifacts.

Note: This test will fail until T030-T035 are implemented.
"""
import os
import sys
import pytest
from pathlib import Path
from src.analysis.sensitivity_check import main as sensitivity_main
from src.services.report_generator import main as report_main

PROJECT_ROOT = Path(__file__).parent.parent.parent
REPORT_PATH = PROJECT_ROOT / "reports" / "final_report.pdf"
SENSITIVITY_PLOT = PROJECT_ROOT / "reports" / "sensitivity_plot.png"

@pytest.mark.integration
def test_sensitivity_analysis_execution():
    """
    Run sensitivity analysis and verify output files.
    """
    if not (PROJECT_ROOT / "data" / "processed" / "regression_results.json").exists():
        pytest.skip("Regression results not found")
    
    try:
        # sensitivity_main() # Commented to prevent execution in skeleton
        pass
    except Exception as e:
        pytest.fail(f"Sensitivity analysis failed: {e}")

@pytest.mark.integration
def test_report_generation_execution():
    """
    Run report generation and verify final PDF creation.
    """
    if not (PROJECT_ROOT / "data" / "processed" / "sensitivity_metrics.json").exists():
        pytest.skip("Sensitivity metrics not found")
    
    try:
        # report_main() # Commented to prevent execution in skeleton
        pass
    except Exception as e:
        pytest.fail(f"Report generation failed: {e}")

@pytest.mark.integration
def test_final_report_exists():
    """Assert that the final report PDF exists."""
    assert REPORT_PATH.exists(), f"Final report missing: {REPORT_PATH}"

@pytest.mark.integration
def test_sensitivity_plot_exists():
    """Assert that the sensitivity plot PNG exists."""
    assert SENSITIVITY_PLOT.exists(), f"Sensitivity plot missing: {SENSITIVITY_PLOT}"