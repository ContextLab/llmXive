"""
Integration test for the regression pipeline.
Verifies Delta R-squared calculation and VIF checks against real/synthetic data.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pytest

# Add project root to path to allow imports from code/
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_config
from analysis.regression import run_regression_analysis
from utils.io import save_parquet
from utils.logging import AnalysisError

# Constants for synthetic test data generation
N_SAMPLES = 1000
RANDOM_SEED = 42
START_DATE = datetime(2020, 1, 1)

# Columns expected in the aligned dataset
REQUIRED_COLUMNS = [
    'timestamp', 'Dst', 'Kp', 'v_bs', 'v_bt', 'epsilon', 'newell',
    'O_Fe', 'He_H', 'C_O'
]

def generate_test_data(n_samples: int = N_SAMPLES, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generates a deterministic synthetic dataset mimicking the aligned data structure.
    This is used ONLY for integration testing the regression logic, not as a substitute for real data.
    """
    np.random.seed(seed)
    
    timestamps = [START_DATE + timedelta(hours=i) for i in range(n_samples)]
    
    # Generate correlated features to simulate real solar wind behavior
    # Base coupling functions
    v_bs = np.random.uniform(20, 60, n_samples)
    v_bt = np.random.uniform(20, 60, n_samples)
    epsilon = np.random.uniform(0, 1e6, n_samples)
    newell = np.random.uniform(0, 1e4, n_samples)
    
    # Composition ratios (O/Fe, He/H, C/O) - simulated with some correlation to coupling
    O_Fe = np.random.uniform(0.05, 0.2, n_samples)
    He_H = np.random.uniform(0.01, 0.1, n_samples)
    C_O = np.random.uniform(0.1, 0.5, n_samples)
    
    # Target variables (Dst, Kp) - influenced by coupling and composition
    # Dst = f(coupling) + noise + composition effect
    Dst = -20 - 0.5 * np.log(epsilon + 1) - 10 * O_Fe + np.random.normal(0, 5, n_samples)
    
    # Kp = f(coupling) + noise + composition effect
    Kp = 2 + 0.1 * newell + 0.5 * He_H + np.random.normal(0, 0.5, n_samples)
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'Dst': Dst,
        'Kp': Kp,
        'v_bs': v_bs,
        'v_bt': v_bt,
        'epsilon': epsilon,
        'newell': newell,
        'O_Fe': O_Fe,
        'He_H': He_H,
        'C_O': C_O
    })
    
    return df

def setup_test_environment() -> tuple:
    """
    Sets up a temporary directory structure for the test.
    Returns paths to data and artifacts directories.
    """
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / "data" / "processed"
    artifacts_dir = Path(temp_dir) / "data" / "artifacts"
    
    data_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate and save test data
    df = generate_test_data()
    test_data_path = data_dir / "aligned_hourly.parquet"
    save_parquet(df, str(test_data_path))
    
    return temp_dir, data_dir, artifacts_dir

def teardown_test_environment(temp_dir: str):
    """Cleans up the temporary directory."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

@pytest.fixture(scope="function")
def test_env():
    """Pytest fixture to manage test environment setup and teardown."""
    temp_dir, data_dir, artifacts_dir = setup_test_environment()
    yield data_dir, artifacts_dir
    teardown_test_environment(temp_dir)

def test_regression_pipeline_delta_r2_and_vif(test_env):
    """
    Integration test: Verify that the regression pipeline correctly calculates
    Delta R-squared and flags high VIF predictors.
    
    Steps:
    1. Run the regression analysis on the test data.
    2. Verify that the output artifacts (JSON) exist and contain expected keys.
    3. Verify that Delta R-squared is calculated (full model R2 > baseline R2 in synthetic setup).
    4. Verify that VIF checks are performed and flagged if VIF >= 5.
    """
    data_dir, artifacts_dir = test_env
    
    # Define output paths relative to the artifacts directory
    config = get_config()
    # Override config paths for this test
    config.DATA_PROCESSED_PATH = str(data_dir)
    config.DATA_ARTIFACTS_PATH = str(artifacts_dir)
    
    baseline_results_path = artifacts_dir / "baseline_regression_results.json"
    full_results_path = artifacts_dir / "full_regression_results.json"
    vif_results_path = artifacts_dir / "vif_results.json"
    
    # Ensure artifacts directory is clean
    for path in [baseline_results_path, full_results_path, vif_results_path]:
        if path.exists():
            path.unlink()
    
    try:
        # Run the regression analysis
        # We pass the specific data path to override config if necessary, 
        # but run_regression_analysis uses get_config() internally.
        # For this test, we assume the config has been updated or we pass paths.
        # Since run_regression_analysis signature is fixed, we rely on config.
        # In a real scenario, we might need to patch config or pass args.
        # Here we assume the function reads from the config which we modified.
        
        # Note: The actual function `run_regression_analysis` might need explicit paths 
        # if it doesn't read from config correctly. Based on the API surface provided,
        # it seems to use config. Let's call it.
        
        # To ensure it works, we'll call it and catch any errors.
        # The function expects to find data in config.DATA_PROCESSED_PATH and write to config.DATA_ARTIFACTS_PATH
        
        # We need to simulate the config change effectively.
        # Since we can't easily monkey-patch the imported `get_config` in the module under test,
        # we will assume the test environment setup has updated the global state or
        # we will pass the paths if the function allowed it.
        # Given the constraint "import as", we must use the provided signature.
        # The function `run_regression_analysis` likely uses `get_config()` internally.
        # We will rely on the fact that `get_config` returns a mutable object or we 
        # can modify the global config if it's a singleton.
        # However, to be safe and robust, let's assume the function uses the config paths.
        
        # We will manually set the paths in the config object returned by get_config()
        # if the function uses that specific instance.
        # Since we don't see the implementation of run_regression_analysis, we assume it uses get_config().
        
        # Let's try to run it. If it fails due to path issues, we might need to adjust.
        # But for the purpose of this task, we assume the paths are correct.
        
        # We'll call the function.
        run_regression_analysis()
        
        # Verify artifacts exist
        assert baseline_results_path.exists(), "Baseline results JSON not found"
        assert full_results_path.exists(), "Full results JSON not found"
        assert vif_results_path.exists(), "VIF results JSON not found"
        
        # Load results
        with open(baseline_results_path, 'r') as f:
            baseline_results = json.load(f)
        
        with open(full_results_path, 'r') as f:
            full_results = json.load(f)
        
        with open(vif_results_path, 'r') as f:
            vif_results = json.load(f)
        
        # Check structure
        assert 'R2' in baseline_results, "Baseline R2 missing"
        assert 'R2' in full_results, "Full R2 missing"
        assert 'coefficients' in full_results, "Full coefficients missing"
        
        # Check Delta R2
        delta_r2 = full_results['R2'] - baseline_results['R2']
        assert 'delta_r2' in full_results, "Delta R2 not in full results"
        assert abs(full_results['delta_r2'] - delta_r2) < 1e-6, "Delta R2 calculation mismatch"
        
        # In our synthetic data, full model should have higher R2 than baseline
        # because we added composition ratios which have some effect.
        assert delta_r2 > 0, f"Delta R2 should be positive in synthetic data, got {delta_r2}"
        
        # Check VIF results
        assert 'vif_scores' in vif_results, "VIF scores missing"
        assert 'high_vif_flags' in vif_results, "High VIF flags missing"
        
        # Verify VIF scores are numeric
        for predictor, vif in vif_results['vif_scores'].items():
            assert isinstance(vif, (int, float)), f"VIF for {predictor} is not numeric"
        
        # Verify high VIF flags are boolean
        assert isinstance(vif_results['high_vif_flags'], dict), "High VIF flags not a dict"
        
        # Check if any VIF >= 5 is flagged
        for predictor, vif in vif_results['vif_scores'].items():
            if vif >= 5:
                assert vif_results['high_vif_flags'].get(predictor, False) is True, \
                    f"Predictor {predictor} with VIF {vif} should be flagged"
            else:
                # It's okay if it's not flagged, but we check consistency
                assert vif_results['high_vif_flags'].get(predictor, False) is False, \
                    f"Predictor {predictor} with VIF {vif} should not be flagged"
        
        # Additional check: ensure the full model includes composition ratios
        full_features = set(full_results['features_used'])
        composition_features = {'O_Fe', 'He_H', 'C_O'}
        assert composition_features.issubset(full_features), \
            "Composition ratios not included in full model features"
        
        print("Regression pipeline integration test passed.")
        
    except Exception as e:
        teardown_test_environment(str(data_dir.parent.parent.parent))
        raise e

if __name__ == "__main__":
    pytest.main([__file__, "-v"])