import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis import fit_lmm, fit_random_intercept_model, run_analysis_pipeline
from config import set_seed

@pytest.fixture
def sample_data():
    """Generate sample data for testing."""
    set_seed(42)
    n = 200
    data = pd.DataFrame({
        "duration_estimate": np.random.normal(10, 2, n),
        "surprisal": np.random.normal(0.5, 0.2, n),
        "sequence_length": np.random.randint(1, 10, n),
        "modality": np.random.choice(["visual", "auditory"], n),
        "participant_id": [f"P{i%20}" for i in range(n)]
    })
    return data

def test_fallback_model_creation(sample_data):
    """Test that the fallback random-intercept model can be created."""
    # Force a scenario where full model might fail or just test the fallback function directly
    # We test that the function returns a valid model object
    try:
        model = fit_random_intercept_model(sample_data)
        assert model is not None
        assert hasattr(model, 'params')
    except Exception as e:
        # If even the fallback fails, it should raise an error, not return None silently
        pytest.fail(f"Fallback model creation failed unexpectedly: {e}")

def test_analysis_pipeline_convergence_handling(sample_data, tmp_path):
    """Test that the pipeline handles convergence and logs status."""
    # Mock data file
    data_file = tmp_path / "standardized.csv"
    sample_data.to_csv(data_file, index=False)
    
    # Run pipeline
    results = run_analysis_pipeline(data_file)
    
    # Verify results structure
    assert "convergence_status" in results
    assert "model_type" in results
    assert results["convergence_status"] in ["converged", "fallback_used"]
    
    # Verify fallback logic is present (even if full model converges, the check exists)
    assert "convergence_threshold" in results
    assert results["convergence_threshold"] == 0.90

def test_mde_calculation(sample_data):
    """Test MDE calculation returns a float."""
    from analysis import calculate_mde
    mde = calculate_mde(sample_data)
    assert isinstance(mde, float)
    assert mde >= 0