"""
Unit tests for plotting utilities in src.analysis.plots
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import numpy as np

from src.analysis.plots import (
    load_raw_mse_data,
    aggregate_mse_by_position_and_quantizer,
    compute_cumulative_mse,
    plot_error_accumulation_divergence
)


def test_load_raw_mse_data_valid_file():
    """Test loading valid JSONL MSE data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"token_position": 1, "mse": 0.5, "quantizer_type": "KVarN"}\n')
        f.write('{"token_position": 2, "mse": 0.6, "quantizer_type": "KVarN"}\n')
        f.write('{"token_position": 1, "mse": 0.8, "quantizer_type": "Uniform"}\n')
        temp_path = f.name

    try:
        data = load_raw_mse_data(temp_path)
        assert len(data) == 3
        assert data[0]['token_position'] == 1
        assert data[0]['mse'] == 0.5
        assert data[0]['quantizer_type'] == 'KVarN'
    finally:
        os.unlink(temp_path)


def test_load_raw_mse_data_file_not_found():
    """Test loading from non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_raw_mse_data("/nonexistent/path/file.jsonl")


def test_aggregate_mse_by_position_and_quantizer():
    """Test aggregation logic."""
    data = [
        {"token_position": 1, "mse": 0.5, "quantizer_type": "KVarN"},
        {"token_position": 1, "mse": 0.7, "quantizer_type": "KVarN"},
        {"token_position": 2, "mse": 0.6, "quantizer_type": "Uniform"},
        {"token_position": 1, "mse": 0.8, "quantizer_type": "Uniform"},
    ]
    
    aggregated = aggregate_mse_by_position_and_quantizer(data)
    
    assert 'KVarN' in aggregated
    assert 'Uniform' in aggregated
    assert 1 in aggregated['KVarN']
    assert 2 not in aggregated['KVarN']
    assert 1 in aggregated['Uniform']
    assert 2 in aggregated['Uniform']
    
    # Check values
    assert aggregated['KVarN'][1] == [0.5, 0.7]
    assert aggregated['Uniform'][1] == [0.8]
    assert aggregated['Uniform'][2] == [0.6]


def test_compute_cumulative_mse():
    """Test cumulative MSE calculation."""
    aggregated = {
        'KVarN': {
            1: [0.5, 0.7],  # mean = 0.6
            2: [0.4],       # mean = 0.4
        },
        'Uniform': {
            1: [0.8],       # mean = 0.8
            2: [0.9],       # mean = 0.9
        }
    }
    
    results = compute_cumulative_mse(aggregated)
    
    assert 'KVarN' in results
    assert 'Uniform' in results
    
    kvarn_pos, kvarn_vals = results['KVarN']
    uniform_pos, uniform_vals = results['Uniform']
    
    # Check positions are sorted
    assert list(kvarn_pos) == [1, 2]
    assert list(uniform_pos) == [1, 2]
    
    # Check cumulative means
    assert np.isclose(kvarn_vals[0], 0.6)
    assert np.isclose(kvarn_vals[1], 0.4)
    assert np.isclose(uniform_vals[0], 0.8)
    assert np.isclose(uniform_vals[1], 0.9)


def test_plot_error_accumulation_divergence_creates_file():
    """Test that the plot function creates the output file."""
    # Create temporary input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"token_position": 1, "mse": 0.5, "quantizer_type": "KVarN"}\n')
        f.write('{"token_position": 2, "mse": 0.6, "quantizer_type": "KVarN"}\n')
        f.write('{"token_position": 1, "mse": 0.8, "quantizer_type": "Uniform"}\n')
        f.write('{"token_position": 2, "mse": 0.9, "quantizer_type": "Uniform"}\n')
        input_path = f.name

    output_file = tempfile.mktemp(suffix='.png')
    
    try:
        plot_error_accumulation_divergence(
            data_file=input_path,
            output_file=output_file
        )
        
        assert os.path.exists(output_file)
        assert os.path.getsize(output_file) > 0
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)
        if os.path.exists(output_file):
            os.unlink(output_file)