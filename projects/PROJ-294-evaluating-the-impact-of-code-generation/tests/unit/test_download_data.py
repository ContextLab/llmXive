"""
Unit tests for download_data.py (T010).
"""
import os
import sys
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

import download_data

def test_setup_logging_no_args():
    """Test setup_logging() with no arguments."""
    logger = download_data.setup_logging()
    assert logger is not None
    assert logger.name.startswith("T010")

def test_setup_logging_with_task_id():
    """Test setup_logging(task_id='...')."""
    logger = download_data.setup_logging(task_id="T010")
    assert logger is not None
    assert "T010-T010" in logger.name

def test_calculate_quartile_boundaries_empty():
    """Test quartile calculation with empty data."""
    result = download_data.calculate_quartile_boundaries([])
    assert "Q1" in result
    assert "Q2" in result
    assert "Q3" in result

def test_calculate_quartile_boundaries_with_data():
    """Test quartile calculation with sample data."""
    data = [{"pass_rate": 0.1}, {"pass_rate": 0.5}, {"pass_rate": 0.9}]
    result = download_data.calculate_quartile_boundaries(data)
    assert result["Q1"] <= result["Q2"] <= result["Q3"]

def test_generate_sampling_config():
    """Test sampling config generation."""
    data = [{"task_id": f"task_{i}"} for i in range(10)]
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        config_path = f.name
    
    try:
        config = download_data.generate_sampling_config(data, config_path)
        assert config["sample_size"] == 80
        assert config["random_seed"] == 42
        assert "quartile_boundaries" in config
        
        # Verify file was written
        assert os.path.exists(config_path)
        with open(config_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == config
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)

def test_perform_stratified_sampling():
    """Test sampling logic (non-stratified as per constraints)."""
    data = [{"task_id": f"task_{i}"} for i in range(100)]
    config = {
        "sample_size": 10,
        "random_seed": 42,
        "quartile_boundaries": {"Q1": 0, "Q2": 0.5, "Q3": 1}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        output_path = f.name
    
    try:
        download_data.perform_stratified_sampling(data, config, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            sampled = json.load(f)
        
        assert len(sampled) == 10
        # Check determinism
        download_data.perform_stratified_sampling(data, config, output_path)
        with open(output_path, 'r') as f:
            sampled2 = json.load(f)
        assert sampled == sampled2
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

def test_extract_human_references():
    """Test extraction of human references."""
    data = [
        {
            "task_id": "HumanEval/0",
            "prompt": "def test(): pass",
            "canonical_solution": "def test(): return True",
            "test": "assert test() == True",
            "entry_point": "test"
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        output_path = f.name
    
    try:
        download_data.extract_human_references(data, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            refs = json.load(f)
        
        assert len(refs) == 1
        assert refs[0]["task_id"] == "HumanEval/0"
        assert "canonical_solution" in refs[0]
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)