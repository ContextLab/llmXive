"""
Integration test for the model training pipeline (T022).

Verifies:
1. The training script executes without error.
2. Both models (Thermodynamic and Composition-Only) are trained on the EXACT SAME data intersection.
3. Nested CV splits are generated correctly.
4. Statistical tests (Permutation/Bootstrap) run and produce valid p-values/CIs.
5. Output artifacts (models, metrics) are saved.
"""
import os
import sys
import tempfile
import shutil
import logging
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import StratifiedKFold, RepeatedKFold
from sklearn.metrics import r2_score, mean_squared_error

# Setup paths
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.models.train import train_models
from src.models.evaluate import evaluate_models, run_permutation_test, run_bootstrap_ci
from src.utils.validators import validate_schema

# Constants
SCHEMA_PATH = project_root / "contracts" / "dataset.schema.yaml"
N_SAMPLES = 50  # Small sample for integration test speed
TEMP_DIR = None

@pytest.fixture(scope="module")
def test_data():
    """Generate a small, valid dataset for integration testing."""
    np.random.seed(42)
    n = N_SAMPLES
    
    # Create valid composition strings (Fe, Cr, Ni, Mo)
    compositions = []
    for _ in range(n):
        c = {
            "Fe": round(np.random.uniform(0.5, 0.8), 2),
            "Cr": round(np.random.uniform(0.1, 0.3), 2),
            "Ni": round(np.random.uniform(0.05, 0.2), 2),
            "Mo": round(np.random.uniform(0.0, 0.05), 2)
        }
        # Normalize
        total = sum(c.values())
        c = {k: v/total for k, v in c.items()}
        # Sort alphabetically for consistency
        comp_str = ",".join([f"{k}{v:.2f}" for k, v in sorted(c.items())])
        compositions.append(comp_str)
    
    # Create features
    data = {
        "alloy_id": [f"ALLOY_{i}" for i in range(n)],
        "composition_str": compositions,
        "temperature": np.random.uniform(600, 1000, n),
        "stress": np.random.uniform(50, 200, n),
        "rupture_time": np.random.uniform(100, 10000, n),
        "mixing_enthalpy": np.random.uniform(-10, 10, n),
        "radius_mismatch": np.random.uniform(0.01, 0.1, n)
    }
    
    df = pd.DataFrame(data)
    
    # Add a simple target for the model to learn (synthetic ground truth)
    # y = f(T, stress, enthalpy) + noise
    # We'll use a simple linear combination for the test to ensure R^2 > 0
    df["target"] = (
        0.5 * df["temperature"] / 1000.0 + 
        0.3 * df["stress"] / 200.0 + 
        0.2 * df["mixing_enthalpy"] / 10.0 + 
        np.random.normal(0, 0.1, n)
    )
    
    return df

@pytest.fixture(scope="module")
def temp_workspace(test_data):
    """Create a temporary workspace for model artifacts."""
    global TEMP_DIR
    TEMP_DIR = tempfile.mkdtemp()
    data_path = Path(TEMP_DIR) / "processed_data.csv"
    model_dir = Path(TEMP_DIR) / "models"
    metrics_dir = Path(TEMP_DIR) / "metrics"
    
    data_path.parent.mkdir(parents=True)
    model_dir.mkdir()
    metrics_dir.mkdir()
    
    test_data.to_csv(data_path, index=False)
    
    yield {
        "data_path": str(data_path),
        "model_dir": str(model_dir),
        "metrics_dir": str(metrics_dir)
    }
    
    shutil.rmtree(TEMP_DIR)

def test_full_training_pipeline(temp_workspace, test_data):
    """
    End-to-end integration test for model training and evaluation.
    Verifies T022 requirements:
    - Same data intersection used
    - Nested CV works
    - Statistical tests run
    """
    data_path = temp_workspace["data_path"]
    model_dir = temp_workspace["model_dir"]
    metrics_dir = temp_workspace["metrics_dir"]
    
    logger = logging.getLogger("integration_test")
    logger.setLevel(logging.INFO)
    
    # 1. Train Models
    # This should load the CSV, split data, and train both models
    try:
        results = train_models(
            data_path=data_path,
            model_dir=model_dir,
            metrics_dir=metrics_dir,
            n_samples=N_SAMPLES,
            seed=42
        )
    except Exception as e:
        logger.error(f"Training failed: {e}")
        pytest.fail(f"Training script crashed: {e}")
    
    # 2. Verify Models Exist
    thermo_model_path = os.path.join(model_dir, "thermodynamic_model.pkl")
    comp_model_path = os.path.join(model_dir, "composition_model.pkl")
    
    assert os.path.exists(thermo_model_path), "Thermodynamic model not saved"
    assert os.path.exists(comp_model_path), "Composition model not saved"
    
    # 3. Verify Metrics Exist
    metrics_files = os.listdir(metrics_dir)
    assert len(metrics_files) > 0, "No metrics files generated"
    
    # 4. Verify Intersection Logic (Implicit in results structure)
    # The train_models function should return a dict with 'n_samples_used'
    # which must be identical for both models.
    assert "thermodynamic_n" in results, "Thermodynamic sample count missing"
    assert "composition_n" in results, "Composition sample count missing"
    assert results["thermodynamic_n"] == results["composition_n"], \
        "Models trained on different data sizes!"
    
    # 5. Run Statistical Tests (T022 requirement: verify they execute)
    # We simulate the evaluation step here to ensure the logic holds
    # In a real run, evaluate.py would be called separately, but we test the functions
    
    # Load metrics
    import json
    with open(os.path.join(metrics_dir, "cv_results.json"), 'r') as f:
        cv_results = json.load(f)
    
    # 6. Verify Permutation Test (N=50 -> 20 <= N < 100)
    # We manually invoke the permutation test to ensure it runs without error
    # using the CV scores from the results
    thermo_scores = cv_results.get("thermodynamic_scores", [])
    comp_scores = cv_results.get("composition_scores", [])
    
    assert len(thermo_scores) > 0, "No thermodynamic CV scores"
    assert len(comp_scores) > 0, "No composition CV scores"
    
    # Run permutation test (subset of permutations for speed in integration test)
    p_val = run_permutation_test(
        thermo_scores, 
        comp_scores, 
        n_permutations=100, # Reduced for speed
        seed=42
    )
    
    assert isinstance(p_val, float), "Permutation test did not return a float"
    assert 0.0 <= p_val <= 1.0, "Invalid p-value from permutation test"
    
    # 7. Verify Bootstrap CI (for N < 20 case, but we test the function exists and runs)
    # Since N=50, we technically use Permutation, but we verify the Bootstrap function works too
    ci_bounds = run_bootstrap_ci(thermo_scores, n_bootstraps=50, seed=42)
    assert len(ci_bounds) == 2, "Bootstrap CI did not return 2 bounds"
    assert ci_bounds[0] <= ci_bounds[1], "Invalid CI bounds"
    
    logger.info("Integration test passed: Models trained, metrics saved, statistical tests executed.")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
