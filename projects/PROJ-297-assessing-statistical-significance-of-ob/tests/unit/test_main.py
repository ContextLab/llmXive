import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the main module functions
from main import (
    compute_file_hash,
    verify_data_integrity,
    analyze_pvalue_distribution,
    validate_threshold_range,
    check_threshold_sweep_edge_cases,
    verify_variable_counts
)

def test_compute_file_hash(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello World")
    hash_val = compute_file_hash(file_path)
    assert len(hash_val) == 64  # SHA256 hex length
    assert isinstance(hash_val, str)

def test_verify_data_integrity_empty():
    results = {}
    assert not verify_data_integrity(results)

def test_verify_data_integrity_valid():
    results = {
        'datasets_processed': 1,
        'correlation_matrices': [],
        'null_distributions': [],
        'p_values': []
    }
    assert verify_data_integrity(results)

def test_analyze_pvalue_distribution():
    p_values = [0.01, 0.05, 0.5, 0.9]
    dist = analyze_pvalue_distribution(p_values)
    assert dist['count'] == 4
    assert 0.0 <= dist['mean'] <= 1.0

def test_validate_threshold_range():
    assert validate_threshold_range(0.3)
    assert not validate_threshold_range(0.0)
    assert not validate_threshold_range(1.0)
    assert not validate_threshold_range(-0.1)

def test_check_threshold_sweep_edge_cases():
    assert check_threshold_sweep_edge_cases([0.1, 0.5, 0.9])
    assert not check_threshold_sweep_edge_cases([0.0, 0.5])
    assert not check_threshold_sweep_edge_cases([1.0])
    assert not check_threshold_sweep_edge_cases([])

def test_verify_variable_counts():
    import pandas as pd
    df = pd.DataFrame({f"col{i}": range(10) for i in range(25)})
    datasets = [df]
    assert verify_variable_counts(datasets)
    
    df_small = pd.DataFrame({f"col{i}": range(10) for i in range(10)})
    datasets_small = [df_small]
    assert not verify_variable_counts(datasets_small)
