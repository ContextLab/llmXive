import pytest
import pandas as pd
import os
import tempfile
from pathlib import Path
import json

from src.services.analysis import run_full_analysis
from src.lib.config import get_processed_data_path, get_artifacts_path

@pytest.fixture
def temp_final_dataset():
    """Create a temporary final_analysis_dataset.parquet for testing."""
    # This fixture assumes the file exists from a previous run or creates a minimal valid one
    # For the purpose of this test, we check if the file exists.
    # If not, we skip or create a mock one that passes schema (if allowed)
    # But T037 says "Input: data/processed/final_analysis_dataset.parquet".
    # If the file is missing, the test should fail or skip.
    # Given the "Execution Failed" context, we assume the file should exist.
    # We will create a minimal valid dataframe if the real one is missing to allow the test to run
    # and check the logic, but in a real CI, it should be the real file.
    # However, the instruction says "NEVER fabricate results".
    # So we will check for the file. If missing, we skip.
    path = get_processed_data_path("final_analysis_dataset.parquet")
    if not path.exists():
        pytest.skip("final_analysis_dataset.parquet not found. Run embeddings step first.")
    return path

def test_binned_analysis_execution(temp_final_dataset):
    """
    Integration test for full statistical pipeline.
    Input: data/processed/final_analysis_dataset.parquet
    Assertions: Verify p-values are present, corrected, and the report contains the "associational" label.
    Verification: Assert artifacts/results/analysis_report.md exists and contains "associational",
    and artifacts/results/corrected_pvalues.json exists.
    """
    # Run the analysis
    results = run_full_analysis(temp_final_dataset)

    # Check results structure
    assert "correlations" in results
    assert "regression" in results
    assert "p_values" in results

    # Check corrected p-values file
    corrected_pvalues_path = get_artifacts_path("corrected_pvalues.json")
    assert corrected_pvalues_path.exists(), "corrected_pvalues.json was not created"

    with open(corrected_pvalues_path, 'r') as f:
        pvalues_data = json.load(f)
    
    assert "method" in pvalues_data
    assert "raw_pvalues" in pvalues_data
    assert "corrected_pvalues" in pvalues_data
    assert "significant_count" in pvalues_data

    # Check report file
    report_path = get_artifacts_path("analysis_report.md")
    assert report_path.exists(), "analysis_report.md was not created"

    with open(report_path, 'r') as f:
        report_content = f.read()

    assert "associational" in report_content.lower(), "Report must contain 'associational'"
    assert "causal" not in report_content.lower(), "Report must NOT contain 'causal'"
    
    # Verify p-values are present in the report (basic check)
    assert "p-value" in report_content.lower() or "p value" in report_content.lower()