"""
Tests for T025: Integration of Ingestion and Feature Engineering.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the integration script's main logic components
# We cannot import main() directly if it calls sys.exit, so we test the helper functions
# or mock the environment.
from features import (
    calculate_per_sample_stats,
    calculate_global_entanglement_score,
    calculate_dimensional_fidelity_loss,
    load_aligned_data
)

@pytest.fixture
def sample_data():
    """Create a temporary parquet file with mock data for testing."""
    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        pytest.skip("pandas and numpy required for this test")

    # Create mock data
    n_samples = 10
    data = {
        "sample_id": [f"sample_{i}" for i in range(n_samples)],
        "teacher_logits": [
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.5, 0.5, 0.5], # Zero variance
            [1.0, 2.0, 3.0, 4.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.2, 0.4, 0.6, 0.8],
            [0.1, 0.1, 0.1, 0.1],
            [0.3, 0.3, 0.3, 0.3],
            [0.4, 0.5, 0.6, 0.7],
            [0.8, 0.9, 1.0, 1.1],
            [0.0, 0.1, 0.2, 0.3]
        ],
        "student_scalar": [0.25, 0.5, 2.5, 0.0, 0.5, 0.1, 0.3, 0.55, 0.95, 0.15],
        "primary_dimension": ["Alignment"] * n_samples,
        "human_Alignment": [0.25, 0.5, 2.5, 0.0, 0.5, 0.1, 0.3, 0.55, 0.95, 0.15],
        "human_Realism": [0.3, 0.4, 3.0, 0.1, 0.6, 0.2, 0.4, 0.6, 1.0, 0.2],
        "human_Aesthetics": [0.4, 0.5, 3.5, 0.2, 0.7, 0.3, 0.5, 0.65, 1.05, 0.25],
        "human_Plauisibility": [0.5, 0.6, 4.0, 0.3, 0.8, 0.4, 0.6, 0.7, 1.1, 0.3]
    }
    
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
        df.to_parquet(tmp.name)
        return tmp.name

def test_per_sample_stats():
    sample = {
        "teacher_logits": [1.0, 2.0, 3.0, 4.0]
    }
    stats = calculate_per_sample_stats(sample)
    
    assert "variance" in stats
    assert "entropy" in stats
    assert "skewness" in stats
    assert "kurtosis" in stats
    
    # Check variance for [1,2,3,4]
    # Mean = 2.5, Vars = [2.25, 0.25, 0.25, 2.25], Sum = 5.0, n-1=3 -> 5/3 = 1.666...
    assert abs(stats["variance"] - 1.6666666) < 0.001

def test_per_sample_stats_zero_variance():
    sample = {
        "teacher_logits": [1.0, 1.0, 1.0, 1.0]
    }
    stats = calculate_per_sample_stats(sample)
    
    assert stats["variance"] == 0.0
    assert stats["entropy"] == 0.0 # Or close to 0 depending on implementation

def test_global_entanglement_score(sample_data):
    # Load data
    data = list(load_aligned_data(sample_data))
    
    eig = calculate_global_entanglement_score(data)
    
    assert isinstance(eig, float)
    assert eig >= 0.0 # Variance/Covariance eigenvalues should be non-negative

def test_dimensional_fidelity_loss():
    sample = {
        "student_scalar": 0.5,
        "primary_dimension": "Alignment",
        "human_annotations": {
            "Alignment": 0.6,
            "Realism": 0.7
        }
    }
    
    loss = calculate_dimensional_fidelity_loss(sample)
    assert loss == 0.1

def test_dimensional_fidelity_loss_missing_dimension():
    sample = {
        "student_scalar": 0.5,
        "primary_dimension": "Alignment",
        "human_annotations": {
            "Realism": 0.7
        }
    }
    
    with pytest.raises(KeyError):
        calculate_dimensional_fidelity_loss(sample)

def test_integration_pipeline(sample_data):
    """
    Test the full flow: Load -> Compute Global -> Compute Per-Sample -> Merge -> Output.
    This simulates what integrate_features.py does.
    """
    data = list(load_aligned_data(sample_data))
    
    # Global
    global_eig = calculate_global_entanglement_score(data)
    
    # Per-sample
    results = []
    for s in data:
        stats = calculate_per_sample_stats(s)
        loss = calculate_dimensional_fidelity_loss(s)
        results.append({
            "sample_id": s.get("sample_id"),
            "variance": stats["variance"],
            "entropy": stats["entropy"],
            "dominant_eigenvalue": global_eig,
            "fidelity_loss": loss
        })
    
    # Validate structure
    assert len(results) == len(data)
    for r in results:
        assert "sample_id" in r
        assert "variance" in r
        assert "dominant_eigenvalue" in r
        assert "fidelity_loss" in r
        # Check that global eigenvalue is consistent across all samples
        assert r["dominant_eigenvalue"] == global_eig

def teardown_module(module):
    # Cleanup temp files if created in fixture
    pass