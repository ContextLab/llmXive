import pytest
from pathlib import Path
import csv
import json
import tempfile
import shutil

# Import the functions we're testing
from generation.pipeline import (
    calculate_pass_rates,
    detect_significant_bias,
    check_model_incapability,
    inject_bias_flag_to_csv,
    SUBSTANTIAL_THRESHOLD,
    MIN_PASS_RATE_THRESHOLD
)

@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file for testing."""
    csv_path = tmp_path / "samples_all.csv"
    data = [
        {"task_id": "0", "style": "neutral", "sample_id": "0_neutral_0", "code": "def f(): pass", "pass_status": "True"},
        {"task_id": "0", "style": "neutral", "sample_id": "0_neutral_1", "code": "def f(): pass", "pass_status": "True"},
        {"task_id": "0", "style": "pep8", "sample_id": "0_pep8_0", "code": "def f(): pass", "pass_status": "True"},
        {"task_id": "0", "style": "pep8", "sample_id": "0_pep8_1", "code": "def f(): pass", "pass_status": "False"},
        {"task_id": "0", "style": "minified", "sample_id": "0_minified_0", "code": "def f():pass", "pass_status": "False"},
    ]
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    return csv_path

def test_calculate_pass_rates(sample_csv):
    """Test that pass rates are calculated correctly."""
    rates = calculate_pass_rates(sample_csv)
    
    assert 'neutral' in rates
    assert 'pep8' in rates
    assert 'minified' in rates
    
    # neutral: 2/2 = 100%
    assert rates['neutral'] == 1.0
    
    # pep8: 1/2 = 50%
    assert rates['pep8'] == 0.5
    
    # minified: 0/1 = 0%
    assert rates['minified'] == 0.0

def test_detect_significant_bias_no_bias(sample_csv):
    """Test that no bias is detected when differences are small."""
    # Modify sample_csv to have small differences
    rates = {
        'neutral': 0.5,
        'pep8': 0.55,
        'minified': 0.52
    }
    
    result = detect_significant_bias(rates)
    assert result is None

def test_detect_significant_bias_with_bias(sample_csv):
    """Test that bias is detected when differences exceed threshold."""
    rates = {
        'neutral': 0.9,
        'pep8': 0.1,
        'minified': 0.5
    }
    
    result = detect_significant_bias(rates)
    assert result == "Potentially Biased"

def test_check_model_incapability_capable(sample_csv):
    """Test that model is considered capable when pass rates are high."""
    rates = {
        'neutral': 0.5,
        'pep8': 0.6,
        'minified': 0.4
    }
    
    result = check_model_incapability(rates)
    assert result is False

def test_check_model_incapability_incapable(sample_csv):
    """Test that model is considered incapable when pass rate is too low."""
    rates = {
        'neutral': 0.005,  # 0.5% - below 1% threshold
        'pep8': 0.6,
        'minified': 0.4
    }
    
    result = check_model_incapability(rates)
    assert result is True

def test_inject_bias_flag_to_csv(sample_csv):
    """Test that bias flag is correctly injected into CSV."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        test_csv = tmp_path / "test.csv"
        
        # Copy sample data
        shutil.copy(sample_csv, test_csv)
        
        inject_bias_flag_to_csv(test_csv, "Potentially Biased")
        
        # Verify flag was added
        with open(test_csv, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert 'bias_flag' in reader.fieldnames
            for row in rows:
                assert row['bias_flag'] == "Potentially Biased"

def test_inject_bias_flag_to_csv_no_flag(sample_csv):
    """Test that empty flag is injected when no bias."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        test_csv = tmp_path / "test.csv"
        
        shutil.copy(sample_csv, test_csv)
        
        inject_bias_flag_to_csv(test_csv, None)
        
        with open(test_csv, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert 'bias_flag' in reader.fieldnames
            for row in rows:
                assert row['bias_flag'] == ""