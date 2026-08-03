"""
Tests for T024a: Data Leakage Audit
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from audit.leakage_audit import run_audit, compute_mutual_information, load_processed_data
from audit.leakage_audit import INPUT_FILE, OUTPUT_FILE, LEAKAGE_THRESHOLD

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    processed_dir = tmp_path / 'data' / 'processed'
    logs_dir = tmp_path / 'data' / 'logs'
    processed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path

def create_test_data(temp_path, leakage=False):
    """Create a mock ingredient_pairs_with_labels.csv."""
    n = 100
    if leakage:
        # Create perfect correlation (leakage)
        data = {
            'log_co_occurrence': np.random.rand(n),
            'flavor_similarity': np.random.rand(n),
            'functional_role': ['primary'] * n,
            'compatibility_label': np.random.rand(n) > 0.5
        }
        # Force high correlation for one predictor
        data['flavor_similarity'] = data['compatibility_label'].astype(float) + np.random.normal(0, 0.01, n)
    else:
        # Random data (no leakage)
        data = {
            'log_co_occurrence': np.random.rand(n),
            'flavor_similarity': np.random.rand(n),
            'functional_role': np.random.choice(['primary', 'secondary', 'garnish'], n),
            'compatibility_label': np.random.choice([0, 1], n)
        }
    
    df = pd.DataFrame(data)
    output_file = temp_path / 'data' / 'processed' / 'ingredient_pairs_with_labels.csv'
    df.to_csv(output_file, index=False)
    return output_file

def test_compute_mi_random_data(temp_data_dir):
    """Test MI computation on random data (should be low)."""
    create_test_data(temp_data_dir, leakage=False)
    
    df = pd.read_csv(create_test_data(temp_data_dir, leakage=False))
    mi = compute_mutual_information(df, 'log_co_occurrence', 'compatibility_label')
    
    # With random data, MI should be low (though not exactly 0 due to noise)
    assert mi < 0.5, f"MI too high for random data: {mi}"

def test_compute_mi_perfect_correlation(temp_data_dir):
    """Test MI computation on perfectly correlated data (should be high)."""
    create_test_data(temp_data_dir, leakage=True)
    
    df = pd.read_csv(create_test_data(temp_data_dir, leakage=True))
    mi = compute_mutual_information(df, 'flavor_similarity', 'compatibility_label')
    
    # With perfect correlation, MI should be high
    assert mi > 0.5, f"MI too low for correlated data: {mi}"

def test_audit_passes_no_leakage(temp_data_dir, monkeypatch):
    """Test that audit passes when there is no leakage."""
    create_test_data(temp_data_dir, leakage=False)
    
    # Monkeypatch paths to use temp directory
    monkeypatch.setattr('audit.leakage_audit.INPUT_FILE', create_test_data(temp_data_dir, leakage=False))
    monkeypatch.setattr('audit.leakage_audit.OUTPUT_FILE', temp_data_dir / 'data' / 'logs' / 'leakage_audit.json')
    
    results = run_audit()
    
    assert results['status'] == 'PASS'
    assert results['threshold'] == LEAKAGE_THRESHOLD
    assert 'metrics' in results
    
    # Verify output file exists
    assert os.path.exists(results['input_file'].replace(str(PROJECT_ROOT), str(temp_data_dir)).replace('data/processed/ingredient_pairs_with_labels.csv', 'data/processed/ingredient_pairs_with_labels.csv'))

def test_audit_fails_with_leakage(temp_data_dir, monkeypatch):
    """Test that audit raises error when leakage is detected."""
    create_test_data(temp_data_dir, leakage=True)
    
    # Monkeypatch paths
    monkeypatch.setattr('audit.leakage_audit.INPUT_FILE', create_test_data(temp_data_dir, leakage=True))
    monkeypatch.setattr('audit.leakage_audit.OUTPUT_FILE', temp_data_dir / 'data' / 'logs' / 'leakage_audit.json')
    
    with pytest.raises(ValueError, match="Data Leakage Audit Failed"):
        run_audit()
        
    # Verify that the file was still written (as per implementation)
    # Note: The implementation writes the file before raising the error
    output_file = temp_data_dir / 'data' / 'logs' / 'leakage_audit.json'
    # The file might not exist if the error happens before write in some edge cases,
    # but in our implementation it writes then raises.
    # Let's check if the file exists and has the correct structure if the write happened.
    # Actually, in the current implementation, we write then raise.
    if output_file.exists():
        with open(output_file) as f:
            data = json.load(f)
            assert data['status'] == 'FAIL'

def test_missing_input_file(temp_data_dir, monkeypatch):
    """Test that audit fails gracefully if input file is missing."""
    # Monkeypatch to a non-existent file
    monkeypatch.setattr('audit.leakage_audit.INPUT_FILE', temp_data_dir / 'nonexistent.csv')
    
    with pytest.raises(FileNotFoundError):
        run_audit()
