import csv
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the functions to test
from data.validate_labels import (
    load_manual_labels,
    calculate_cohen_kappa,
    validate_disclosure_signal,
    write_validation_log
)

@pytest.fixture
def temp_manual_labels_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerow(['pr_number', 'manual_label'])
        writer.writerow([1, 'Disclosing'])
        writer.writerow([2, 'Non-Disclosing'])
        writer.writerow([3, 'Disclosing'])
        writer.writerow([4, 'Non-Disclosing'])
        writer.writerow([5, 'Disclosing'])
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_sampled_prs_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerow(['pr_number', 'origin_label', 'other_col'])
        writer.writerow([1, 'Disclosing', 'x'])
        writer.writerow([2, 'Disclosing', 'x']) # Mismatch
        writer.writerow([3, 'Disclosing', 'x'])
        writer.writerow([4, 'Non-Disclosing', 'x'])
        writer.writerow([5, 'Non-Disclosing', 'x']) # Mismatch
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_output_log_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = f.name
    os.unlink(temp_path) # Remove empty file so append works cleanly
    return temp_path

def test_load_manual_labels(temp_manual_labels_file):
    labels = load_manual_labels(temp_manual_labels_file)
    assert len(labels) == 5
    assert labels[1] == 'Disclosing'
    assert labels[2] == 'Non-Disclosing'

def test_load_manual_labels_missing_file():
    with pytest.raises(FileNotFoundError):
        load_manual_labels("non_existent_file.csv")

def test_calculate_cohen_kappa():
    # Perfect agreement
    auto = ['A', 'B', 'A']
    manual = ['A', 'B', 'A']
    kappa = calculate_cohen_kappa(auto, manual)
    assert kappa == 1.0

    # No agreement (completely opposite)
    auto = ['A', 'A', 'A']
    manual = ['B', 'B', 'B']
    kappa = calculate_cohen_kappa(auto, manual)
    # Kappa can be negative if agreement is worse than chance
    assert kappa < 0.5 

def test_validate_disclosure_signal_pass(temp_manual_labels_file, temp_sampled_prs_file, temp_output_log_file):
    # Create a scenario where Kappa should be high
    # Auto: D, D, D, N, N
    # Man:  D, N, D, N, D
    # Matches: 1(D-D), 3(D-D), 4(N-N) -> 3/5 match. 
    # With 2 classes, chance is 0.5. Observed 0.6. Kappa ~ (0.6-0.5)/(1-0.5) = 0.2.
    # Let's make it perfect for the test
    
    # Overwrite temp files with perfect match data
    with open(temp_sampled_prs_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['pr_number', 'origin_label', 'other'])
        writer.writerow([1, 'Disclosing', 'x'])
        writer.writerow([2, 'Non-Disclosing', 'x'])
        writer.writerow([3, 'Disclosing', 'x'])
        writer.writerow([4, 'Non-Disclosing', 'x'])
        writer.writerow([5, 'Disclosing', 'x'])
    
    is_valid, metrics = validate_disclosure_signal(
        temp_sampled_prs_file,
        temp_manual_labels_file,
        temp_output_log_file,
        threshold=0.6
    )
    
    assert is_valid is True
    assert metrics['kappa'] == 1.0
    assert metrics['status'] == 'PASS'
    assert os.path.exists(temp_output_log_file)

def test_validate_disclosure_signal_fail(temp_manual_labels_file, temp_output_log_file):
    # Create a scenario with low agreement
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f_prs:
        writer = csv.writer(f_prs)
        writer.writerow(['pr_number', 'origin_label', 'other'])
        # Manual: D, N, D, N, D
        # Auto:   N, D, N, D, N (Perfectly opposite)
        writer.writerow([1, 'Non-Disclosing', 'x'])
        writer.writerow([2, 'Disclosing', 'x'])
        writer.writerow([3, 'Non-Disclosing', 'x'])
        writer.writerow([4, 'Disclosing', 'x'])
        writer.writerow([5, 'Non-Disclosing', 'x'])
        temp_prs_path = f_prs.name

    try:
        is_valid, metrics = validate_disclosure_signal(
            temp_prs_path,
            temp_manual_labels_file,
            temp_output_log_file,
            threshold=0.6
        )
        # Kappa should be negative, so is_valid should be False
        assert is_valid is False
        assert metrics['status'] == 'FAIL'
        assert metrics['kappa'] < 0.5
    finally:
        os.unlink(temp_prs_path)

def test_write_validation_log(temp_output_log_file):
    metrics = {
        'kappa': 0.85,
        'threshold': 0.6,
        'sample_size': 10,
        'is_valid': True,
        'status': 'PASS'
    }
    write_validation_log(temp_output_log_file, metrics)
    
    assert os.path.exists(temp_output_log_file)
    with open(temp_output_log_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert float(rows[0]['kappa']) == 0.85
        assert rows[0]['status'] == 'PASS'
