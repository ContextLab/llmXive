"""
Unit tests for sensitivity analysis module (T026)
"""
import pytest
import os
import json
import csv
import tempfile
from pathlib import Path

# Import the module under test
from analysis.sensitivity_analysis import (
    load_metrics_with_detector_scores,
    filter_by_detector_cohort,
    run_sensitivity_tests,
    run_sensitivity_analysis
)

@pytest.fixture
def sample_metrics_data():
    """Create sample metrics data with detector scores for testing."""
    data = [
        {'pr_id': 1, 'source_type': 'llm', 'comment_count': 5, 'time_to_merge_minutes': 120.0, 'review_cycles': 2, 'complexity_score': 15.5, 'detector_score': 0.85},
        {'pr_id': 2, 'source_type': 'llm', 'comment_count': 3, 'time_to_merge_minutes': 90.0, 'review_cycles': 1, 'complexity_score': 12.0, 'detector_score': 0.92},
        {'pr_id': 3, 'source_type': 'human', 'comment_count': 8, 'time_to_merge_minutes': 200.0, 'review_cycles': 3, 'complexity_score': 18.2, 'detector_score': 0.75},
        {'pr_id': 4, 'source_type': 'human', 'comment_count': 12, 'time_to_merge_minutes': 300.0, 'review_cycles': 5, 'complexity_score': 22.1, 'detector_score': 0.88},
        {'pr_id': 5, 'source_type': 'llm', 'comment_count': 4, 'time_to_merge_minutes': 100.0, 'review_cycles': 2, 'complexity_score': 10.5, 'detector_score': 0.65},  # Low detector score
        {'pr_id': 6, 'source_type': 'human', 'comment_count': 6, 'time_to_merge_minutes': 150.0, 'review_cycles': 2, 'complexity_score': 14.0, 'detector_score': 0.72},
        {'pr_id': 7, 'source_type': 'llm', 'comment_count': 2, 'time_to_merge_minutes': 60.0, 'review_cycles': 1, 'complexity_score': 8.0, 'detector_score': 0.95},
        {'pr_id': 8, 'source_type': 'human', 'comment_count': 15, 'time_to_merge_minutes': 400.0, 'review_cycles': 6, 'complexity_score': 25.0, 'detector_score': 0.80},
    ]
    return data

@pytest.fixture
def temp_metrics_csv(sample_metrics_data):
    """Create a temporary CSV file with sample metrics data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        fieldnames = ['pr_id', 'source_type', 'comment_count', 'time_to_merge_minutes', 
                     'review_cycles', 'complexity_score', 'detector_score']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in sample_metrics_data:
            writer.writerow(row)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_metrics_with_detector_scores(temp_metrics_csv):
    """Test that metrics are loaded correctly with detector scores."""
    data = load_metrics_with_detector_scores(temp_metrics_csv)
    
    assert len(data) == 8
    assert all('detector_score' in entry for entry in data)
    assert all(isinstance(entry['detector_score'], float) for entry in data)
    assert data[0]['detector_score'] == 0.85
    assert data[4]['detector_score'] == 0.65  # Low score entry

def test_filter_by_detector_cohort_high_threshold(sample_metrics_data):
    """Test filtering with a high threshold (0.8)."""
    filtered = filter_by_detector_cohort(sample_metrics_data, threshold=0.8)
    
    # Should only include entries with detector_score >= 0.8
    assert len(filtered) == 5  # Entries 1, 2, 4, 7, 8
    assert all(entry['detector_score'] >= 0.8 for entry in filtered)
    
    # Verify low score entry is excluded
    assert not any(entry['pr_id'] == 5 for entry in filtered)  # pr_id 5 has score 0.65
    assert not any(entry['pr_id'] == 6 for entry in filtered)  # pr_id 6 has score 0.72

def test_filter_by_detector_cohort_low_threshold(sample_metrics_data):
    """Test filtering with a low threshold (0.6)."""
    filtered = filter_by_detector_cohort(sample_metrics_data, threshold=0.6)
    
    # Should include almost all entries
    assert len(filtered) == 7  # Only pr_id 6 (0.72) might be excluded if threshold was higher
    assert all(entry['detector_score'] >= 0.6 for entry in filtered)

def test_filter_by_detector_cohort_empty_result(sample_metrics_data):
    """Test filtering that results in empty dataset."""
    with pytest.raises(ValueError) as excinfo:
        filter_by_detector_cohort(sample_metrics_data, threshold=0.99)
    assert "No PRs meet the detector score threshold" in str(excinfo.value)

def test_run_sensitivity_tests_basic(sample_metrics_data):
    """Test running sensitivity tests on filtered data."""
    filtered = filter_by_detector_cohort(sample_metrics_data, threshold=0.7)
    metrics_to_test = ['comment_count']
    
    results = run_sensitivity_tests(filtered, metrics_to_test)
    
    assert 'comment_count' in results
    assert 't_statistic' in results['comment_count']
    assert 'p_value' in results['comment_count']
    assert 'effect_size' in results['comment_count']
    assert 'is_significant' in results['comment_count']
    assert results['comment_count']['llm_count'] > 0
    assert results['comment_count']['human_count'] > 0

def test_run_sensitivity_tests_insufficient_data():
    """Test handling of insufficient data in filtered cohort."""
    # Create data with only one group
    data = [
        {'pr_id': 1, 'source_type': 'llm', 'comment_count': 5, 'time_to_merge_minutes': 120.0, 
         'review_cycles': 2, 'complexity_score': 15.5, 'detector_score': 0.85},
        {'pr_id': 2, 'source_type': 'llm', 'comment_count': 3, 'time_to_merge_minutes': 90.0, 
         'review_cycles': 1, 'complexity_score': 12.0, 'detector_score': 0.92},
    ]
    
    results = run_sensitivity_tests(data, ['comment_count'])
    
    assert 'comment_count' in results
    assert results['comment_count']['status'] == 'insufficient_data'
    assert results['comment_count']['llm_count'] == 2
    assert results['comment_count']['human_count'] == 0

def test_filter_preserves_source_types(sample_metrics_data):
    """Test that filtering preserves both LLM and human samples."""
    filtered = filter_by_detector_cohort(sample_metrics_data, threshold=0.7)
    
    llm_count = sum(1 for entry in filtered if entry['source_type'] == 'llm')
    human_count = sum(1 for entry in filtered if entry['source_type'] == 'human')
    
    assert llm_count > 0
    assert human_count > 0
    assert llm_count + human_count == len(filtered)

def test_detector_score_threshold_logic(sample_metrics_data):
    """Test that the threshold logic correctly includes/excludes entries."""
    # Test with threshold 0.75
    filtered = filter_by_detector_cohort(sample_metrics_data, threshold=0.75)
    
    # Entries that should be included (score >= 0.75):
    # pr_id 1: 0.85 ✓
    # pr_id 2: 0.92 ✓
    # pr_id 3: 0.75 ✓ (exactly at threshold)
    # pr_id 4: 0.88 ✓
    # pr_id 7: 0.95 ✓
    # pr_id 8: 0.80 ✓
    # Excluded:
    # pr_id 5: 0.65 ✗
    # pr_id 6: 0.72 ✗
    
    included_ids = [entry['pr_id'] for entry in filtered]
    expected_ids = [1, 2, 3, 4, 7, 8]
    
    assert sorted(included_ids) == sorted(expected_ids)