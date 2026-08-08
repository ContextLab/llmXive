"""
Integration test for T028c: Final Report Generation.
Verifies that the report generation script runs and produces a valid markdown file
with the required sections.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.report_generator import (
    load_stability_metrics,
    load_correlation_results,
    load_permutation_results,
    aggregate_for_report,
    run_full_report_aggregation
)
from code.results_writer import write_final_report
from code.config import RESULTS_DIR

@pytest.fixture
def temp_results_dir():
    """Create a temporary directory for test results."""
    temp_dir = tempfile.mkdtemp()
    # Patch RESULTS_DIR for the test scope if possible, or just use temp_dir directly
    # For this test, we will write to the temp_dir and verify content
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_report_structure_and_sections(temp_results_dir):
    """
    Test that the generated report contains all required sections:
    1. 'Significant Variance Differences'
    2. 'Model Comparison'
    3. 'Correction Methodology'
    4. 'Achieved FDR'
    """
    # Create mock data to simulate the output of previous tasks
    # We need to ensure the aggregation functions can run without crashing on real data structures
    
    # Mock Stability Metrics
    mock_stability = pd.DataFrame({
        'dataset_id': [1, 2, 3],
        'model_name': ['LogisticRegression', 'RandomForest', 'SVC'],
        'mean_accuracy': [0.85, 0.88, 0.82],
        'cv_accuracy': [0.05, 0.03, 0.08],
        'mean_f1': [0.84, 0.87, 0.81],
        'cv_f1': [0.05, 0.03, 0.08],
        'log_variance_accuracy': [-4.0, -3.5, -3.0]
    })

    # Mock Correlation Results
    mock_corr = pd.DataFrame({
        'dataset_id': [1, 2, 3],
        'model_name': ['LogisticRegression', 'RandomForest', 'SVC'],
        'metric_type': ['CV', 'CV', 'CV'],
        'pearson_r': [-0.6, -0.7, -0.5],
        'pearson_p_value': [0.01, 0.005, 0.02],
        'spearman_rho': [-0.65, -0.75, -0.55],
        'spearman_p_value': [0.008, 0.004, 0.015],
        'feature_count': [10, 20, 15],
        'sample_size': [1000, 2000, 1500],
        'regression_slope': [-0.5, -0.6, -0.4],
        'regression_intercept': [2.0, 2.1, 1.9]
    })

    # Mock Permutation Results
    mock_perm = pd.DataFrame({
        'dataset_id': [1, 2, 3],
        'model_a': ['LogisticRegression', 'RandomForest', 'SVC'],
        'model_b': ['RandomForest', 'SVC', 'LogisticRegression'],
        'statistic': [0.02, 0.05, 0.03],
        'raw_p_value': [0.03, 0.01, 0.04],
        'adj_p_value': [0.045, 0.02, 0.06],
        'significant': [True, True, False]
    })

    # Simulate the aggregation process
    report_data = aggregate_for_report(mock_stability, mock_corr, mock_perm)
    full_report_data = run_full_report_aggregation(report_data)

    # Write the report to the temp directory
    output_path = Path(temp_results_dir) / "final_report.md"
    write_final_report(full_report_data, output_path)

    # Verify the file exists
    assert output_path.exists(), "Final report file was not created."

    # Read and verify content
    content = output_path.read_text()
    
    required_sections = [
        "Significant Variance Differences",
        "Model Comparison",
        "Correction Methodology",
        "Achieved FDR"
    ]

    for section in required_sections:
        assert section in content, f"Required section '{section}' not found in report."

    # Verify specific content requirements
    assert "Benjamini-Hochberg" in content, "Correction methodology must mention Benjamini-Hochberg."
    assert "FDR" in content, "Report must mention FDR (False Discovery Rate)."

    print("Report generation test passed.")