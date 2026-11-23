"""
Unit tests for Task T025a: Per-Sample Stats Computation.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# Import the module under test
# We need to ensure the path is in sys.path or use relative imports if structured correctly
# Assuming code/ is in the same directory as tests/ or parent
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from per_sample_stats import compute_per_sample_stats, load_dominant_eigenvalue, integrate_features
from entanglement_scores import calculate_entropy

def test_compute_per_sample_stats_basic():
    """Test basic computation of variance, entropy, skewness, kurtosis."""
    # Create a mock dataframe
    data = {
        'sample_id': [1, 2],
        'Alignment': [5.0, 4.0],
        'Realism': [5.0, 6.0],
        'Aesthetics': [5.0, 5.0],
        'Plausibility': [5.0, 3.0]
    }
    df = pd.DataFrame(data)
    
    # Mock logger
    logger = MagicMock()
    
    result = compute_per_sample_stats(df, logger)
    
    assert len(result) == 2
    assert 'variance' in result.columns
    assert 'entropy' in result.columns
    assert 'skewness' in result.columns
    assert 'kurtosis' in result.columns
    
    # Check sample 1 (constant values)
    # Variance should be 0, Entropy 0, Skewness 0, Kurtosis 0
    row1 = result.iloc[0]
    assert row1['variance'] == 0.0
    assert row1['entropy'] == 0.0
    assert row1['skewness'] == 0.0
    assert row1['kurtosis'] == 0.0

def test_compute_per_sample_stats_missing_dims():
    """Test that missing dimensions raise an error."""
    data = {
        'sample_id': [1],
        'Alignment': [5.0],
        'Realism': [5.0],
        # Missing Aesthetics and Plausibility
    }
    df = pd.DataFrame(data)
    logger = MagicMock()
    
    with pytest.raises(ValueError, match="Missing teacher score dimensions"):
        compute_per_sample_stats(df, logger)

def test_load_dominant_eigenvalue_missing():
    """Test that missing eigenvalue file raises an error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        results_dir = base_path / 'results'
        results_dir.mkdir()
        
        logger = MagicMock()
        
        with pytest.raises(FileNotFoundError, match="Dominant eigenvalue file not found"):
            load_dominant_eigenvalue(logger, base_path)

def test_load_dominant_eigenvalue_success():
    """Test successful loading of dominant eigenvalue."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        results_dir = base_path / 'results'
        results_dir.mkdir()
        
        eigen_path = results_dir / 'dominant_eigenvalue.json'
        with open(eigen_path, 'w') as f:
            json.dump({'dominant_eigenvalue': 12.5}, f)
        
        logger = MagicMock()
        val = load_dominant_eigenvalue(logger, base_path)
        
        assert val == 12.5

def test_entropy_calculation():
    """Test entropy calculation helper."""
    # Uniform distribution
    probs = [0.25, 0.25, 0.25, 0.25]
    ent = calculate_entropy(probs)
    # log2(4) = 2.0
    assert np.isclose(ent, 2.0)
    
    # Deterministic distribution
    probs_det = [1.0, 0.0, 0.0, 0.0]
    ent_det = calculate_entropy(probs_det)
    assert ent_det == 0.0