"""
Unit tests for retrieval_output.py (T020)
"""
import pytest
import os
import json
import tempfile
from pathlib import Path
import numpy as np

from retrieval_output import save_retrieval_results, format_retrieval_results, process_retrieval_results

@pytest.fixture
def sample_results():
    return [
        {
            'planet_name': 'HD 209458 b',
            'water_mixing_ratio': -4.5,
            'uncertainty': 0.2,
            'is_upper_limit': False,
            'detection_limit': -6.0,
            'min_detectable_concentration': -6.5
        },
        {
            'planet_name': 'GJ 1214 b',
            'water_mixing_ratio': -5.0,
            'uncertainty': 0.5,
            'is_upper_limit': True,
            'detection_limit': -5.5,
            'min_detectable_concentration': -6.0
        }
    ]

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_save_retrieval_results_creates_csv(sample_results, temp_output_dir):
    output_path = temp_output_dir / "retrieval_results.csv"
    save_retrieval_results(sample_results, output_path)
    
    assert output_path.exists(), "Output CSV file was not created"
    
    with open(output_path, 'r') as f:
        content = f.read()
    
    # Check headers
    assert "planet_name" in content
    assert "water_mixing_ratio" in content
    assert "uncertainty" in content
    assert "is_upper_limit" in content
    assert "detection_limit" in content
    assert "min_detectable_concentration" in content
    
    # Check data rows
    assert "HD 209458 b" in content
    assert "GJ 1214 b" in content
    assert "-4.5" in content
    assert "True" in content
    assert "False" in content

def test_save_retrieval_results_empty_list(temp_output_dir):
    output_path = temp_output_dir / "empty_results.csv"
    save_retrieval_results([], output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 1  # Only header
    assert "planet_name" in lines[0]

def test_format_retrieval_results_handles_nan():
    results = [
        {
            'planet_name': 'Test Planet',
            'water_mixing_ratio': np.nan,
            'uncertainty': None,
            'is_upper_limit': False,
            'detection_limit': np.nan,
            'min_detectable_concentration': np.nan
        }
    ]
    
    formatted = format_retrieval_results(results)
    
    assert formatted[0]['water_mixing_ratio'] == ""
    assert formatted[0]['uncertainty'] == ""
    assert formatted[0]['is_upper_limit'] == "False"

def test_process_retrieval_results_passes_through(sample_results):
    processed = process_retrieval_results(sample_results)
    assert len(processed) == len(sample_results)
    assert processed[0]['planet_name'] == 'HD 209458 b'