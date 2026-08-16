"""
Unit tests for transform module fallback logic (T050).
Tests that the system correctly handles missing scikit-bio.
"""
import os
import json
import sys
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from transform import (
    apply_clr_transformation,
    ensure_compositionality_flag,
    detect_compositionality,
    transform_data
)

@pytest.fixture
def sample_taxa_data():
    """Create sample taxa abundance data."""
    data = pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3', 'S4'],
        'taxon_A': [0.1, 0.2, 0.15, 0.25],
        'taxon_B': [0.3, 0.25, 0.35, 0.2],
        'taxon_C': [0.6, 0.55, 0.5, 0.55],
        'sleep_duration': [7.5, 8.0, 6.5, 7.0]
    })
    return data

@pytest.fixture
def metadata_dir():
    """Create a temporary metadata directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = Path(tmpdir) / "data" / "metadata"
        metadata_path.mkdir(parents=True)
        # Monkey-patch the path
        original_path = Path("data/metadata")
        # Note: In real tests, we'd mock the path, but for now we use the real one
        # and clean up after
        yield metadata_path
        # Cleanup would happen automatically

def test_apply_clr_with_scikit_bio_available(sample_taxa_data):
    """Test CLR transformation when scikit-bio is available."""
    taxa_cols = ['taxon_A', 'taxon_B', 'taxon_C']
    
    # This test assumes scikit-bio is installed
    try:
        import skbio
        result = apply_clr_transformation(sample_taxa_data, taxa_cols)
        
        # Check that transformation was applied
        assert 'taxon_A' in result.columns
        assert 'taxon_B' in result.columns
        assert 'taxon_C' in result.columns
        
        # Check that flag was written
        flag_path = Path("data/metadata/compositionality_flag.json")
        assert flag_path.exists()
        
        with open(flag_path) as f:
            flag_data = json.load(f)
        
        assert flag_data['method_used'] == 'CLR (scikit-bio)'
        assert flag_data['fallback_used'] is False
        
    except ImportError:
        # If scikit-bio is not available, test the fallback path
        pytest.skip("scikit-bio not available for this test")

def test_apply_clr_fallback_when_scikit_bio_missing(sample_taxa_data, monkeypatch):
    """Test that fallback to log(x+1) works when scikit-bio is missing."""
    taxa_cols = ['taxon_A', 'taxon_B', 'taxon_C']
    
    # Mock ImportError for skbio
    original_import = __builtins__.__import__
    
    def mock_import(name, *args, **kwargs):
        if name == 'skbio' or name.startswith('skbio.'):
            raise ImportError("No module named 'skbio'")
        return original_import(name, *args, **kwargs)
    
    monkeypatch.setattr(__builtins__, '__import__', mock_import)
    
    # Run transformation
    result = apply_clr_transformation(sample_taxa_data, taxa_cols)
    
    # Check that transformation was applied (log(x+1))
    assert 'taxon_A' in result.columns
    assert 'taxon_B' in result.columns
    assert 'taxon_C' in result.columns
    
    # Check that flag was written with fallback info
    flag_path = Path("data/metadata/compositionality_flag.json")
    assert flag_path.exists()
    
    with open(flag_path) as f:
        flag_data = json.load(f)
    
    assert flag_data['fallback_used'] is True
    assert flag_data['fallback_method'] == 'log(x+1) transformation'
    assert 'scikit-bio' in flag_data.get('fallback_reason', '')

def test_detect_compositionality_true(sample_taxa_data):
    """Test detection of compositional data (sums to 1)."""
    taxa_cols = ['taxon_A', 'taxon_B', 'taxon_C']
    
    # Data sums to 1.0
    is_comp = detect_compositionality(sample_taxa_data, taxa_cols)
    assert is_comp is True

def test_detect_compositionality_false():
    """Test detection of non-compositional data."""
    data = pd.DataFrame({
        'sample_id': ['S1', 'S2'],
        'taxon_A': [100, 200],
        'taxon_B': [150, 250]
    })
    
    taxa_cols = ['taxon_A', 'taxon_B']
    is_comp = detect_compositionality(data, taxa_cols)
    assert is_comp is False

def test_transform_data_compositional(sample_taxa_data):
    """Test full transformation pipeline for compositional data."""
    taxa_cols = ['taxon_A', 'taxon_B', 'taxon_C']
    
    result = transform_data(sample_taxa_data, taxa_cols)
    
    # Check that all columns are preserved
    assert 'sample_id' in result.columns
    assert 'sleep_duration' in result.columns
    assert 'taxon_A' in result.columns
    assert 'taxon_B' in result.columns
    assert 'taxon_C' in result.columns

def test_ensure_compositionality_flag_creates_file():
    """Test that ensure_compositionality_flag creates the flag file."""
    flag_path = Path("data/metadata/compositionality_flag.json")
    
    # Ensure directory exists
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove if exists
    if flag_path.exists():
        flag_path.unlink()
    
    ensure_compositionality_flag(method="test", fallback_used=False)
    
    assert flag_path.exists()
    
    with open(flag_path) as f:
        flag_data = json.load(f)
    
    assert flag_data['method_used'] == 'test'
    assert flag_data['fallback_used'] is False
    assert 'timestamp' in flag_data
