import pytest
import pandas as pd
from pathlib import Path
import json
import tempfile
import os
from code import _data_streaming
from code._data_streaming import load_imageNet_streaming, load_laion_streaming
from code.utils.config import get_config
import sys

# Mock the module to be tested
import importlib.util
spec = importlib.util.spec_from_file_location("validate_sources", "code/00_validate_sources.py")
validate_sources_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_sources_module)

def test_validate_sources_both_present():
    """Test validation passes when both sources are present."""
    df = pd.DataFrame({
        'source': ['imagenet-1k', 'laion-400m', 'imagenet-1k'],
        'data': [1, 2, 3]
    })
    
    is_valid, message, counts = validate_sources_module.validate_sources(df)
    
    assert is_valid is True
    assert 'imagenet-1k' in counts
    assert 'laion-400m' in counts
    assert len(counts) == 2

def test_validate_sources_missing_laion():
    """Test validation fails when LAION is missing."""
    df = pd.DataFrame({
        'source': ['imagenet-1k', 'imagenet-1k'],
        'data': [1, 2]
    })
    
    is_valid, message, counts = validate_sources_module.validate_sources(df)
    
    assert is_valid is False
    assert 'Missing required sources' in message
    assert 'laion-400m' in message

def test_validate_sources_missing_imagenet():
    """Test validation fails when ImageNet is missing."""
    df = pd.DataFrame({
        'source': ['laion-400m', 'laion-400m'],
        'data': [1, 2]
    })
    
    is_valid, message, counts = validate_sources_module.validate_sources(df)
    
    assert is_valid is False
    assert 'Missing required sources' in message
    assert 'imagenet-1k' in message

def test_validate_sources_missing_column():
    """Test validation fails when source column is missing."""
    df = pd.DataFrame({
        'data': [1, 2],
        'value': [3, 4]
    })
    
    is_valid, message, counts = validate_sources_module.validate_sources(df)
    
    assert is_valid is False
    assert "missing 'source' column" in message

def test_run_validation_integration():
    """Integration test for run_validation with a temporary file."""
    # Create a temporary parquet file with valid data
    with tempfile.TemporaryDirectory() as tmpdir:
        dataset_path = Path(tmpdir) / "test_dataset.parquet"
        report_path = Path(tmpdir) / "test_report.json"
        
        df = pd.DataFrame({
            'source': ['imagenet-1k', 'laion-400m', 'imagenet-1k', 'laion-400m'],
            'embedding': [[0.1] * 768 for _ in range(4)],
            'routing_label': ['exp1', 'exp2', 'exp1', 'exp2']
        })
        df.to_parquet(dataset_path)
        
        # Run validation
        class Args:
            dataset_path = str(dataset_path)
            report_path = str(report_path)
        
        result = validate_sources_module.run_validation(Args())
        
        assert result == 0
        assert report_path.exists()
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert report['is_valid'] is True
        assert report['total_rows'] == 4
        assert 'imagenet-1k' in report['source_counts']
        assert 'laion-400m' in report['source_counts']

def test_run_validation_fails_missing_file():
    """Test run_validation fails when dataset file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dataset_path = Path(tmpdir) / "nonexistent.parquet"
        
        class Args:
            dataset_path = str(dataset_path)
            report_path = None
        
        result = validate_sources_module.run_validation(Args())
        
        assert result == 1
