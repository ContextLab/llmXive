"""
Integration Test for T041: CI Pipeline Execution.

This test verifies that the full pipeline can be executed end-to-end
and produces the required final report artifact.
"""
import os
import json
import pytest
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_PATH = PROJECT_ROOT / 'docs' / 'final_analysis_report.md'

@pytest.mark.integration
def test_full_pipeline_execution():
    """
    Execute the full pipeline on the seed dataset in CI.
    
    Verifies:
    1. The pipeline script runs without errors.
    2. The final report artifact is generated.
    3. The report contains expected sections.
    """
    # Ensure the report does not exist from a previous run (clean state)
    if REPORT_PATH.exists():
        REPORT_PATH.unlink()
    
    # Run the CI pipeline script
    pipeline_script = PROJECT_ROOT / 'code' / 'analysis' / 'run_ci_pipeline.py'
    
    result = subprocess.run(
        [sys.executable, str(pipeline_script)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    # Assert the script ran successfully
    assert result.returncode == 0, f"Pipeline failed with error:\n{result.stderr}"
    
    # Assert the final report exists
    assert REPORT_PATH.exists(), "Final report artifact was not generated."
    
    # Assert the report is not empty
    assert REPORT_PATH.stat().st_size > 0, "Final report is empty."
    
    # Read and validate report content
    with open(REPORT_PATH, 'r') as f:
        content = f.read()
    
    # Check for required sections
    required_sections = [
        "Executive Summary",
        "Main Model Coefficients",
        "Robustness Checks",
        "Limitations",
        "Appendix"
    ]
    
    for section in required_sections:
        assert section in content, f"Report missing required section: {section}"
    
    # Verify no error messages in the report
    assert "ERROR" not in content.upper() or "error" not in content.lower(), \
        "Report contains error messages."
    
    # Verify the report contains actual data (not just headers)
    assert "Coefficient" in content or "p-value" in content.lower(), \
        "Report does not contain expected statistical results."

@pytest.mark.integration
def test_pipeline_artifacts_exist():
    """
    Verify that all intermediate artifacts required for the report exist.
    """
    required_files = [
        'data/processed/repo_metrics_clean.csv',
        'data/processed/model_results_raw.json',
        'data/processed/robustness_results.json',
        'data/processed/robustness_lagged_results.json'
    ]
    
    for file_rel in required_files:
        file_path = PROJECT_ROOT / file_rel
        assert file_path.exists(), f"Required artifact missing: {file_rel}"
        assert file_path.stat().st_size > 0, f"Required artifact is empty: {file_rel}"
    
    # Verify model results JSON structure
    model_results_path = PROJECT_ROOT / 'data' / 'processed' / 'model_results_raw.json'
    with open(model_results_path, 'r') as f:
        model_results = json.load(f)
    
    assert 'author_count_coefficient' in model_results, "Missing author_count_coefficient"
    assert 'p_value' in model_results, "Missing p_value"
    assert 'std_err' in model_results, "Missing std_err"
    
    # Verify robustness results JSON structure
    robustness_path = PROJECT_ROOT / 'data' / 'processed' / 'robustness_results.json'
    with open(robustness_path, 'r') as f:
        robustness = json.load(f)
    
    assert 'adjusted_p_values' in robustness, "Missing adjusted_p_values"
    assert 'subsample_results' in robustness, "Missing subsample_results"
    assert 'entropy_results' in robustness, "Missing entropy_results"
    assert 'lagged_results' in robustness, "Missing lagged_results"