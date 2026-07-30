"""
Unit tests for T040: Final Analysis Report Generator.

Tests verify:
1. The report generator loads data correctly.
2. The citation is correctly embedded.
3. The output files are created and contain expected content.
"""

import os
import sys
import tempfile
import shutil
import json
import pandas as pd
from pathlib import Path
import pytest

# Adjust path to include project code
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data" / "processed"

sys.path.insert(0, str(PROJECT_ROOT))

from report import (
    generate_report_summary,
    write_text_report,
    write_json_report,
    load_results_metrics,
    load_stability_report,
    load_binned_learners,
    VERIFIED_CITATION
)

@pytest.fixture
def mock_data_dirs():
    """Create temporary directories for test data."""
    temp_dir = tempfile.mkdtemp()
    data_processed = Path(temp_dir) / "processed"
    data_processed.mkdir(parents=True, exist_ok=True)
    
    # Create mock data files
    learners_data = pd.DataFrame({
        "learner_id": [1, 2, 3],
        "feedback_group": ["Immediate", "Delayed", "Variable"]
    })
    (data_processed / "learners_binned.csv").to_csv(learners_data, index=False)

    metrics_data = pd.DataFrame({
        "comparison": ["Immediate vs Delayed"],
        "effect_size": [0.45],
        "p_value": [0.001],
        "significant": [True],
        "target_effect_size": [0.3]
    })
    (data_processed / "results_metrics.csv").to_csv(metrics_data, index=False)

    stability_data = pd.DataFrame({
        "stability_metric": [0.95],
        "flip_rate": [0.0]
    })
    (data_processed / "significance_stability_report.csv").to_csv(stability_data, index=False)

    yield data_processed

    # Cleanup
    shutil.rmtree(temp_dir)

def test_load_results_metrics(mock_data_dirs):
    """Test loading results metrics."""
    # Temporarily override the global path for testing
    import report
    original_path = report.DATA_PROCESSED_DIR
    report.DATA_PROCESSED_DIR = mock_data_dirs
    
    df = load_results_metrics()
    assert df is not None
    assert "effect_size" in df.columns
    
    report.DATA_PROCESSED_DIR = original_path

def test_load_stability_report(mock_data_dirs):
    """Test loading stability report."""
    import report
    original_path = report.DATA_PROCESSED_DIR
    report.DATA_PROCESSED_DIR = mock_data_dirs
    
    df = load_stability_report()
    assert df is not None
    assert "flip_rate" in df.columns
    
    report.DATA_PROCESSED_DIR = original_path

def test_load_binned_learners(mock_data_dirs):
    """Test loading binned learners."""
    import report
    original_path = report.DATA_PROCESSED_DIR
    report.DATA_PROCESSED_DIR = mock_data_dirs
    
    df = load_binned_learners()
    assert df is not None
    assert "feedback_group" in df.columns
    
    report.DATA_PROCESSED_DIR = original_path

def test_generate_report_summary(mock_data_dirs):
    """Test summary generation logic."""
    import report
    original_path = report.DATA_PROCESSED_DIR
    report.DATA_PROCESSED_DIR = mock_data_dirs
    
    metrics = load_results_metrics()
    stability = load_stability_report()
    learners = load_binned_learners()
    
    summary = generate_report_summary(metrics, stability, learners)
    
    assert "citation" in summary
    assert summary["citation"]["doi"] == VERIFIED_CITATION["doi"]
    assert summary["statistical_findings"]["effect_size_cohens_d"] == 0.45
    assert summary["sensitivity_analysis"]["flip_rate"] == 0.0
    assert len(summary["conclusions"]) > 0
    
    report.DATA_PROCESSED_DIR = original_path

def test_write_text_report_creates_file(mock_data_dirs, tmp_path):
    """Test that text report file is created."""
    import report
    original_path = report.DATA_PROCESSED_DIR
    report.DATA_PROCESSED_DIR = mock_data_dirs
    
    # Create a temporary output path for this test
    test_txt = tmp_path / "test_report.txt"
    test_json = tmp_path / "test_report.json"
    
    # Mock the output paths
    report.REPORT_OUTPUT_TXT = test_txt
    report.REPORT_OUTPUT_JSON = test_json
    
    metrics = load_results_metrics()
    stability = load_stability_report()
    learners = load_binned_learners()
    summary = generate_report_summary(metrics, stability, learners)
    
    write_text_report(summary)
    
    assert test_txt.exists()
    content = test_txt.read_text()
    assert "FINAL ANALYSIS REPORT" in content
    assert VERIFIED_CITATION["title"] in content
    
    report.DATA_PROCESSED_DIR = original_path
    report.REPORT_OUTPUT_TXT = report.DATA_PROCESSED_DIR / "final_analysis_report.txt"
    report.REPORT_OUTPUT_JSON = report.DATA_PROCESSED_DIR / "final_analysis_report.json"

def test_write_json_report_creates_file(mock_data_dirs, tmp_path):
    """Test that JSON report file is created and is valid JSON."""
    import report
    original_path = report.DATA_PROCESSED_DIR
    report.DATA_PROCESSED_DIR = mock_data_dirs
    
    test_txt = tmp_path / "test_report.txt"
    test_json = tmp_path / "test_report.json"
    
    report.REPORT_OUTPUT_TXT = test_txt
    report.REPORT_OUTPUT_JSON = test_json
    
    metrics = load_results_metrics()
    stability = load_stability_report()
    learners = load_binned_learners()
    summary = generate_report_summary(metrics, stability, learners)
    
    write_json_report(summary)
    
    assert test_json.exists()
    with open(test_json, 'r') as f:
        data = json.load(f)
    assert "citation" in data
    assert "statistical_findings" in data
    
    report.DATA_PROCESSED_DIR = original_path
    report.REPORT_OUTPUT_TXT = report.DATA_PROCESSED_DIR / "final_analysis_report.txt"
    report.REPORT_OUTPUT_JSON = report.DATA_PROCESSED_DIR / "final_analysis_report.json"