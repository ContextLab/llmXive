import pytest
import pickle
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.train import get_project_root, calculate_null_model_r2

def test_null_model_r2_calculation():
    """Test that null model R2 is calculated correctly."""
    y = [1.0, 2.0, 3.0, 4.0, 5.0]
    r2 = calculate_null_model_r2(y)
    # Null model predicts mean (3.0).
    # SS_res = sum((y - mean)^2) = 10
    # SS_tot = sum((y - mean)^2) = 10
    # R2 = 1 - (10/10) = 0.0
    assert abs(r2 - 0.0) < 1e-6

def test_model_save_load():
    """Test that the model can be saved and loaded."""
    from sklearn.ensemble import GradientBoostingRegressor
    import tempfile
    
    model = GradientBoostingRegressor()
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as f:
        pickle.dump(model, f)
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            loaded_model = pickle.load(f)
        assert loaded_model is not None
    finally:
        os.unlink(temp_path)
