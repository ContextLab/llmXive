import pytest
import pandas as pd
import numpy as np
import sys
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.xgboost_model import tune_and_train, TRAINING_BUDGET_SECONDS

@pytest.fixture
def sample_curated_data():
    """Create a small sample dataset for testing."""
    np.random.seed(42)
    n = 50
    data = {
        'laser_power': np.random.uniform(100, 400, n),
        'scan_speed': np.random.uniform(200, 1000, n),
        'hatch_spacing': np.random.uniform(50, 200, n),
        'layer_thickness': np.random.uniform(20, 50, n),
        'alloy_family': np.random.choice(['Inconel', 'Hastelloy', 'Co-Cr'], n),
        'ductility': np.random.uniform(5, 30, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_curated_csv(tmp_path, sample_curated_data):
    """Create a temporary CSV file with sample data."""
    csv_path = tmp_path / "curated_builds.csv"
    sample_curated_data.to_csv(csv_path, index=False)
    return csv_path

def test_placeholder_models():
    """Placeholder test to ensure test file structure."""
    assert True

def test_vif_calculation_logic():
    """Test VIF calculation logic (placeholder)."""
    assert True

def test_mixed_effects_convergence_check():
    """Test mixed effects convergence check (placeholder)."""
    assert True

def test_save_split_artifacts_logic():
    """Test save split artifacts logic (placeholder)."""
    assert True

def test_xgboost_training_time_budget():
    """
    Integration test for model training time budget.
    Ensures that tune_and_train completes within the specified budget.
    """
    # Create synthetic data for the test
    np.random.seed(42)
    n_samples = 100
    X = np.random.rand(n_samples, 5)
    y = np.random.rand(n_samples)
    
    # Create a small validation set
    X_val = np.random.rand(20, 5)
    y_val = np.random.rand(20)
    
    budget = 300  # Use a smaller budget for testing, should be well under 600
    start_time = time.time()
    
    # Run the training function
    try:
        model, info = tune_and_train(X, y, X_val, y_val, budget_seconds=budget)
        elapsed = time.time() - start_time
        
        # Assert that it completed within the budget
        assert elapsed <= budget, f"Training took {elapsed:.2f}s, which exceeds the budget of {budget}s"
        assert model is not None, "Model was not returned"
        assert 'best_params' in info, "Tuning info missing best_params"
        
    except TimeoutError:
        # If it times out, that's a failure of the function logic, not the test
        pytest.fail("Training timed out unexpectedly")
    except Exception as e:
        # If training fails for other reasons, re-raise to see the error
        pytest.fail(f"Training failed with error: {e}")

def test_placeholder_time_budget():
    """Placeholder test for time budget logic."""
    assert True
