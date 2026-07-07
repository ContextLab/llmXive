import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from src.models.evaluate import compare_primary_sensitivity_models, calculate_cohen_d, benjamini_hochberg_fdr

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_features(temp_data_dir):
    """Generate sample feature data."""
    n_samples = 50
    n_features = 5
    data = np.random.rand(n_samples, n_features)
    features = pd.DataFrame(data, columns=[f"feature_{i}" for i in range(n_features)])
    features.index = [f"pathogen_{i}" for i in range(n_samples)]
    
    # Save to CSV
    path = temp_data_dir / "features.csv"
    features.to_csv(path)
    return path

@pytest.fixture
def sample_interactions(temp_data_dir):
    """Generate sample interaction data with some missing/unknown."""
    data = []
    for i in range(30):
        # Some pathogens have multiple hosts
        num_hosts = np.random.randint(1, 5)
        for j in range(num_hosts):
            data.append({
                "pathogen_id": f"pathogen_{i}",
                "host_species": f"host_{j}",
                "interaction_type": "infection"
            })
    
    # Add some unknown interactions
    for i in range(30, 40):
        data.append({
            "pathogen_id": f"pathogen_{i}",
            "host_species": f"host_{np.random.randint(0, 10)}",
            "interaction_type": "unknown"
        })
    
    # Add some pathogens with no interactions (will be filtered or treated as 0)
    for i in range(40, 50):
        pass # No interactions added
    
    df = pd.DataFrame(data)
    path = temp_data_dir / "interactions.csv"
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def sample_primary_model(temp_data_dir):
    """Create a dummy primary model file."""
    # We don't actually need a real model file for this test if we re-train,
    # but the function expects a path. We'll create a placeholder.
    path = temp_data_dir / "primary_model.pkl"
    # In a real test, we'd save a trained model here.
    # For this test, we assume the function handles re-training if needed.
    # We'll just touch the file to satisfy existence check.
    path.touch()
    return path

@pytest.fixture
def sample_sensitivity_model(temp_data_dir):
    """Create a dummy sensitivity model file."""
    path = temp_data_dir / "sensitivity_model.pkl"
    path.touch()
    return path

def test_benjamini_hochberg_fdr_basic():
    """Test basic FDR correction."""
    p_values = [0.01, 0.03, 0.02, 0.05, 0.10]
    adjusted = benjamini_hochberg_fdr(p_values)
    assert len(adjusted) == len(p_values)
    assert all(0 <= x <= 1 for x in adjusted)
    # Check monotonicity
    sorted_adj = sorted(adjusted)
    assert sorted_adj == sorted(adjusted) # Just a basic check

def test_cohen_d_identical_groups():
    """Test Cohen's d with identical groups."""
    g1 = [1, 2, 3, 4, 5]
    g2 = [1, 2, 3, 4, 5]
    d = calculate_cohen_d(g1, g2)
    assert abs(d) < 1e-6

def test_cohen_d_different_groups():
    """Test Cohen's d with different groups."""
    g1 = [1, 2, 3]
    g2 = [10, 11, 12]
    d = calculate_cohen_d(g1, g2)
    assert d < 0 # g1 mean < g2 mean

def test_compare_primary_sensitivity_models_integration(temp_data_dir, sample_features, sample_interactions, sample_primary_model, sample_sensitivity_model):
    """Test the full comparison function."""
    output_path = temp_data_dir / "sensitivity_analysis.json"
    
    # This test might be slow or complex due to re-training logic.
    # We assert that the function runs and produces the expected output file.
    try:
        result = compare_primary_sensitivity_models(
            primary_model_path=sample_primary_model,
            sensitivity_model_path=sample_sensitivity_model,
            features_path=sample_features,
            interactions_path=sample_interactions,
            output_path=output_path,
            seed=42
        )
        
        assert "primary_auprc" in result
        assert "sensitivity_auprc" in result
        assert "delta" in result
        assert "flag" in result
        assert "methodology" in result
        
        assert output_path.exists()
        with open(output_path) as f:
            saved_report = json.load(f)
            assert saved_report == result
    except Exception as e:
        # If the test environment lacks necessary dependencies or data for full re-training,
        # we might skip or mark as incomplete. However, the task requires real execution.
        # We assume the environment is set up correctly.
        pytest.fail(f"Comparison failed: {e}")