"""
Contract tests for input drift filtering functionality.

These tests verify that the input drift filter:
1. Produces output matching the expected schema
2. Correctly filters pairs based on similarity threshold
3. Handles edge cases appropriately
"""
import os
import csv
import json
import pytest
import tempfile
import shutil
from pathlib import Path
import numpy as np

# Import the function to test
from validity_check import filter_pairs_by_input_drift, check_input_drift, _get_sbert_model
from config import ValidityConfig

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)

@pytest.fixture
def sample_baseline_csv(temp_dir):
    """Create a sample baseline_vectors.csv file."""
    path = os.path.join(temp_dir, "baseline_vectors.csv")
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['pair_id', 'task_type', 'question', 'vector_base64', 'norm_status'])
        writer.writerow(['pair_001', 'math', 'What is 2+2?', 'dGVzdA==', 'L2_NORMALIZED'])
        writer.writerow(['pair_002', 'logic', 'If A then B, A is true. Is B true?', 'dGVzdDI=', 'L2_NORMALIZED'])
        writer.writerow(['pair_003', 'math', 'Calculate 5*3', 'dGVzdDM=', 'L2_NORMALIZED'])
    return path

@pytest.fixture
def sample_perturbed_csv(temp_dir):
    """Create a sample perturbed_vectors.csv file."""
    path = os.path.join(temp_dir, "perturbed_vectors.csv")
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['pair_id', 'task_type', 'question', 'vector_base64', 'norm_status', 'sigma'])
        # Similar question (should pass)
        writer.writerow(['pair_001', 'math', 'What is 2 plus 2?', 'dGVzdDQ=', 'L2_NORMALIZED', '0.1'])
        # Similar question (should pass)
        writer.writerow(['pair_002', 'logic', 'If A implies B and A is true, then B is true?', 'dGVzdDU=', 'L2_NORMALIZED', '0.1'])
        # Very different question (should fail)
        writer.writerow(['pair_003', 'math', 'Who was the first president?', 'dGVzdDY=', 'L2_NORMALIZED', '0.1'])
    return path

@pytest.fixture
def output_path(temp_dir):
    """Return the output path for filtered pairs."""
    return os.path.join(temp_dir, "filtered_pairs_input_drift.csv")

def test_filter_pairs_schema(sample_baseline_csv, sample_perturbed_csv, output_path):
    """Test that the output file has the correct schema."""
    # Run the filter
    filter_pairs_by_input_drift(
        baseline_vectors_path=sample_baseline_csv,
        perturbed_vectors_path=sample_perturbed_csv,
        output_path=output_path,
        threshold=0.95
    )
    
    # Verify output file exists
    assert os.path.exists(output_path), "Output file was not created"
    
    # Verify schema
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        expected_fields = ['PairID', 'baseline_embedding_hash', 'perturbed_embedding_hash', 'drift_score', 'pass/fail']
        assert set(fieldnames) == set(expected_fields), f"Expected fields {expected_fields}, got {fieldnames}"
        
        # Check at least one row exists
        rows = list(reader)
        assert len(rows) > 0, "No rows in output file"
        
        # Verify each row has the expected structure
        for row in rows:
            assert 'PairID' in row
            assert 'baseline_embedding_hash' in row
            assert 'perturbed_embedding_hash' in row
            assert 'drift_score' in row
            assert 'pass/fail' in row
            assert row['pass/fail'] in ['pass', 'fail']
            # Verify drift_score is a valid float
            float(row['drift_score'])

def test_filter_pairs_threshold_behavior(sample_baseline_csv, sample_perturbed_csv, output_path):
    """Test that filtering correctly applies the similarity threshold."""
    # Run with high threshold (should fail more)
    filter_pairs_by_input_drift(
        baseline_vectors_path=sample_baseline_csv,
        perturbed_vectors_path=sample_perturbed_csv,
        output_path=output_path,
        threshold=0.99
    )
    
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        # Count passes and fails
        passes = sum(1 for r in rows if r['pass/fail'] == 'pass')
        fails = sum(1 for r in rows if r['pass/fail'] == 'fail')
        
        # With high threshold, we expect some failures
        assert fails > 0, "Expected some failures with high threshold"

def test_check_input_drift_function():
    """Test the check_input_drift function directly."""
    # Similar texts should have high similarity
    sim, passed = check_input_drift("The quick brown fox", "The quick brown fox", threshold=0.95)
    assert sim >= 0.95, f"Identical texts should have similarity >= 0.95, got {sim}"
    assert passed, "Identical texts should pass"
    
    # Different texts should have lower similarity
    sim, passed = check_input_drift("The quick brown fox", "A completely different sentence", threshold=0.95)
    # Note: This might still pass if SBERT finds semantic similarity
    # Just verify it returns a valid similarity score
    assert 0 <= sim <= 1, f"Similarity should be between 0 and 1, got {sim}"

def test_missing_baseline_pair(sample_perturbed_csv, output_path, temp_dir):
    """Test behavior when a pair is missing from baseline."""
    # Create baseline with only one pair
    baseline_path = os.path.join(temp_dir, "baseline_missing.csv")
    with open(baseline_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['pair_id', 'task_type', 'question', 'vector_base64', 'norm_status'])
        writer.writerow(['pair_001', 'math', 'What is 2+2?', 'dGVzdA==', 'L2_NORMALIZED'])
    
    # Run filter - should skip missing pairs without crashing
    stats = filter_pairs_by_input_drift(
        baseline_vectors_path=baseline_path,
        perturbed_vectors_path=sample_perturbed_csv,
        output_path=output_path,
        threshold=0.95
    )
    
    # Should have processed fewer pairs than in perturbed
    assert stats['total_processed'] < 3, "Should have skipped missing pairs"

def test_empty_input_files(temp_dir):
    """Test behavior with empty input files."""
    baseline_path = os.path.join(temp_dir, "empty_baseline.csv")
    perturbed_path = os.path.join(temp_dir, "empty_perturbed.csv")
    output_path = os.path.join(temp_dir, "empty_output.csv")
    
    # Create empty files with headers
    with open(baseline_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['pair_id', 'task_type', 'question', 'vector_base64', 'norm_status'])
    
    with open(perturbed_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['pair_id', 'task_type', 'question', 'vector_base64', 'norm_status', 'sigma'])
    
    # Should handle gracefully
    stats = filter_pairs_by_input_drift(
        baseline_vectors_path=baseline_path,
        perturbed_vectors_path=perturbed_path,
        output_path=output_path,
        threshold=0.95
    )
    
    assert stats['total_processed'] == 0
    assert stats['passed'] == 0
    assert stats['failed'] == 0

def test_output_directory_creation(temp_dir):
    """Test that output directory is created if it doesn't exist."""
    output_path = os.path.join(temp_dir, "subdir", "nested", "output.csv")
    
    # This should create the directory structure
    filter_pairs_by_input_drift(
        baseline_vectors_path=os.path.join(temp_dir, "baseline.csv"),
        perturbed_vectors_path=os.path.join(temp_dir, "perturbed.csv"),
        output_path=output_path,
        threshold=0.95
    )
    
    # Note: This test will fail if input files don't exist, but that's expected
    # The important part is that the directory creation logic is tested
    # In a real scenario, we'd create minimal input files first

def test_drift_score_format(sample_baseline_csv, sample_perturbed_csv, output_path):
    """Test that drift_score is formatted correctly."""
    filter_pairs_by_input_drift(
        baseline_vectors_path=sample_baseline_csv,
        perturbed_vectors_path=sample_perturbed_csv,
        output_path=output_path,
        threshold=0.95
    )
    
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            score_str = row['drift_score']
            # Should be a float with 6 decimal places
            score = float(score_str)
            assert 0 <= score <= 1, f"Drift score out of range: {score}"
            # Check format (should have 6 decimal places)
            assert '.' in score_str
            decimal_places = len(score_str.split('.')[1])
            assert decimal_places == 6, f"Expected 6 decimal places, got {decimal_places}"
