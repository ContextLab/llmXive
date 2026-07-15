"""
Integration tests for T015: FR-013 narrative note insertion.
"""
import json
import os
import tempfile
import pytest
from datetime import datetime

# Ensure we can import from the project root
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.main import run_pipeline, RESULTS_DIR

def test_t015_permutation_note_insertion():
    """
    Verify that the FR-013 narrative note is inserted into the JSON report
    only if the permutation test was successfully executed.
    """
    # Use a small, recent date range that should have data
    start_date = "2023-01-01"
    end_date = "2023-01-02"
    
    # Run the pipeline
    report = run_pipeline(start_date, end_date)
    
    # Check that the report contains the notes field
    assert 'notes' in report, "Report must contain 'notes' field"
    
    # Check that the permutation test was attempted
    assert 'permutation_test' in report
    assert 'success' in report['permutation_test']
    
    # If permutation test succeeded, the note must be present
    if report['permutation_test']['success']:
        expected_note = "Note: Bonferroni correction is conservative for autocorrelated lag searches; the permutation test (FR-005) is the primary method for significance testing. Future work should consider adaptive FDR control."
        assert expected_note in report['notes'], (
            f"Expected FR-013 note not found in notes. "
            f"Notes: {report['notes']}"
        )
    else:
        # If permutation test failed, the note should NOT be present
        expected_note = "Note: Bonferroni correction is conservative for autocorrelated lag searches; the permutation test (FR-005) is the primary method for significance testing. Future work should consider adaptive FDR control."
        assert expected_note not in report['notes'], (
            "FR-013 note should not be present when permutation test failed"
        )

def test_t015_report_structure():
    """
    Verify the overall structure of the JSON report includes all required fields.
    """
    start_date = "2023-01-01"
    end_date = "2023-01-02"
    
    report = run_pipeline(start_date, end_date)
    
    required_keys = [
        'metadata', 'physics_lag', 'correlation', 
        'optimal_lag', 'permutation_test', 'sensitivity_analysis', 'notes'
    ]
    
    for key in required_keys:
        assert key in report, f"Missing required key: {key}"

def test_t015_quality_log_created():
    """
    Verify that data/processed/quality_log.json is created (T016).
    """
    start_date = "2023-01-01"
    end_date = "2023-01-02"
    
    # Run pipeline
    run_pipeline(start_date, end_date)
    
    # Check for quality log
    quality_log_path = os.path.join(RESULTS_DIR, "quality_log.json")
    assert os.path.exists(quality_log_path), f"Quality log not found at {quality_log_path}"
    
    # Verify it's valid JSON
    with open(quality_log_path, 'r') as f:
        log_data = json.load(f)
    
    assert 'timestamp' in log_data
    assert 'warnings' in log_data or 'data_quality_issues' in log_data
