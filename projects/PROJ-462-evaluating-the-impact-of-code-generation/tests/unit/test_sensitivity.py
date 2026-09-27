"""
Unit tests for sensitivity analysis module.

Tests FR-009 and SC-005 implementation.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import os

# Import the module under test
from analysis.sensitivity import (
    classify_experience,
    run_sensitivity_sweep,
    generate_sensitivity_report,
    run_sensitivity_pipeline,
    ThresholdResult,
    SensitivityReport
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n = 200
    data = {
        'experience_years': np.random.exponential(scale=3.0, size=n),
        'tool_usage': np.random.choice(['copilot', 'traditional'], n),
        'task_time': np.random.normal(loc=100, scale=20, size=n),
        'defect_rate': np.random.normal(loc=0.05, scale=0.02, size=n)
    }
    # Ensure non-negative values
    data['experience_years'] = np.maximum(data['experience_years'], 0.1)
    data['task_time'] = np.maximum(data['task_time'], 10)
    data['defect_rate'] = np.maximum(np.minimum(data['defect_rate'], 1.0), 0.0)

    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for output files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir

def test_classify_experience_thresholds(sample_data):
    """Test experience classification with different thresholds."""
    # Test with threshold 2.0 (novice < 2)
    classification = classify_experience(sample_data, 2.0, 5.0)

    assert 'novice' in classification.values
    assert 'intermediate' in classification.values
    assert 'expert' in classification.values

    # Verify novice count
    novice_count = (classification == 'novice').sum()
    assert novice_count > 0

    # Verify intermediate count
    intermediate_count = (classification == 'intermediate').sum()
    assert intermediate_count > 0

    # Verify expert count
    expert_count = (classification == 'expert').sum()
    assert expert_count > 0

def test_classify_experience_boundaries(sample_data):
    """Test that classification respects boundaries correctly."""
    # Create data with known values at boundaries
    boundary_data = pd.DataFrame({
        'experience_years': [1.0, 1.9, 2.0, 2.1, 4.9, 5.0, 5.1]
    })

    classification = classify_experience(boundary_data, 2.0, 5.0)

    # 1.0, 1.9 should be novice (< 2.0)
    assert classification.iloc[0] == 'novice'
    assert classification.iloc[1] == 'novice'

    # 2.0, 2.1, 4.9 should be intermediate (>= 2.0, < 5.0)
    assert classification.iloc[2] == 'intermediate'
    assert classification.iloc[3] == 'intermediate'
    assert classification.iloc[4] == 'intermediate'

    # 5.0, 5.1 should be expert (>= 5.0)
    assert classification.iloc[5] == 'expert'
    assert classification.iloc[6] == 'expert'

def test_run_sensitivity_sweep_basic(sample_data):
    """Test basic sensitivity sweep execution."""
    thresholds = [1.0, 2.0, 3.0]
    results = run_sensitivity_sweep(sample_data, thresholds)

    assert len(results) == 3
    assert all(isinstance(r, ThresholdResult) for r in results)

    # Check that results have expected attributes
    for r in results:
        assert hasattr(r, 'threshold_years')
        assert hasattr(r, 'novice_count')
        assert hasattr(r, 'mean_task_time_novice')
        assert hasattr(r, 'anova_p_value')
        assert r.threshold_years in thresholds

def test_run_sensitivity_sweep_threshold_order(sample_data):
    """Test that results are ordered by threshold."""
    thresholds = [3.0, 1.0, 2.0]  # Unordered input
    results = run_sensitivity_sweep(sample_data, thresholds)

    # Results should maintain input order
    assert results[0].threshold_years == 3.0
    assert results[1].threshold_years == 1.0
    assert results[2].threshold_years == 2.0

def test_generate_sensitivity_report_structure(sample_data):
    """Test that report generation creates correct structure."""
    thresholds = [2.0]
    results = run_sensitivity_sweep(sample_data, thresholds)
    report = generate_sensitivity_report(results, thresholds)

    assert isinstance(report, SensitivityReport)
    assert report.thresholds_tested == thresholds
    assert len(report.results) == 1
    assert 'analysis_timestamp' in dir(report)
    assert 'summary' in dir(report)

def test_sensitivity_report_summary(sample_data):
    """Test that report summary contains expected metrics."""
    thresholds = [1.0, 2.0, 3.0]
    results = run_sensitivity_sweep(sample_data, thresholds)
    report = generate_sensitivity_report(results, thresholds)

    assert 'total_thresholds_tested' in report.summary
    assert report.summary['total_thresholds_tested'] == 3
    assert 'p_value_range' in report.summary
    assert 'interaction_p_value_range' in report.summary
    assert 'stability_assessment' in report.summary

def test_run_sensitivity_pipeline_io(temp_output_dir, sample_data):
    """Test full pipeline with file I/O."""
    input_path = temp_output_dir / "input.csv"
    output_path = temp_output_dir / "sensitivity_report.json"

    sample_data.to_csv(input_path, index=False)

    # Run pipeline
    report = run_sensitivity_pipeline(
        str(input_path),
        str(output_path),
        thresholds=[1.5, 2.5]
    )

    # Verify output file exists
    assert output_path.exists()

    # Verify JSON structure
    with open(output_path, 'r') as f:
        json_data = json.load(f)

    assert 'analysis_timestamp' in json_data
    assert 'thresholds_tested' in json_data
    assert 'results' in json_data
    assert 'summary' in json_data
    assert len(json_data['results']) == 2

def test_run_sensitivity_pipeline_missing_columns(temp_output_dir, sample_data):
    """Test pipeline fails gracefully with missing columns."""
    input_path = temp_output_dir / "incomplete.csv"
    output_path = temp_output_dir / "output.json"

    # Create data missing a required column
    incomplete_data = sample_data.drop(columns=['tool_usage'])
    incomplete_data.to_csv(input_path, index=False)

    with pytest.raises(ValueError, match="Missing required columns"):
        run_sensitivity_pipeline(str(input_path), str(output_path))

def test_run_sensitivity_pipeline_missing_file(temp_output_dir):
    """Test pipeline fails when input file doesn't exist."""
    output_path = temp_output_dir / "output.json"

    with pytest.raises(FileNotFoundError):
        run_sensitivity_pipeline(
            str(temp_output_dir / "nonexistent.csv"),
            str(output_path)
        )

def test_effect_size_calculation_in_sweep(sample_data):
    """Test that effect sizes are calculated in sensitivity sweep."""
    thresholds = [2.0]
    results = run_sensitivity_sweep(sample_data, thresholds)

    # At least some effect sizes should be calculated if sample sizes are sufficient
    # We don't assert specific values, just that the fields exist and are populated
    if results[0].novice_count > 5 and results[0].intermediate_count > 5:
        assert results[0].cohens_d_novice_vs_intermediate is not None
    if results[0].intermediate_count > 5 and results[0].expert_count > 5:
        assert results[0].cohens_d_intermediate_vs_expert is not None

def test_empty_threshold_list(sample_data):
    """Test handling of empty threshold list."""
    thresholds = []
    results = run_sensitivity_sweep(sample_data, thresholds)

    assert len(results) == 0

def test_single_threshold(sample_data):
    """Test with a single threshold."""
    thresholds = [2.0]
    results = run_sensitivity_sweep(sample_data, thresholds)

    assert len(results) == 1
    assert results[0].threshold_years == 2.0