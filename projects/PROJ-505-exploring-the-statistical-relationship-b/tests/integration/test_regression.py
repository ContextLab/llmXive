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
    
    # Override config paths for this test
    config = get_config()
    # The test mutates the config dict by adding attributes; we store the overrides
    # in module‑level constants used by the regression module.
    # The regression module reads PROC_DIR and ARTIFACT_DIR from config, so we patch them.
    from code import config as cfg_module
    cfg_module.PROC_DIR = data_dir
    cfg_module.ARTIFACT_DIR = artifacts_dir
    
    # Run the regression analysis
    run_regression_analysis()
    
    # Verify artifacts exist
    baseline_results_path = artifacts_dir / "baseline_regression_results.json"
    full_results_path = artifacts_dir / "full_regression_results.json"
    vif_results_path = artifacts_dir / "vif_results.json"
    
    assert baseline_results_path.exists(), "Baseline results JSON not found"
    assert full_results_path.exists(), "Full results JSON not found"
    assert vif_results_path.exists(), "VIF results JSON not found"
    
    # Load results
    with baseline_results_path.open('r') as f:
        baseline_results = json.load(f)
    
    with full_results_path.open('r') as f:
        full_results = json.load(f)
    
    with vif_results_path.open('r') as f:
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
            assert vif_results['high_vif_flags'].get(predictor, False) is False, \
                f"Predictor {predictor} with VIF {vif} should not be flagged"
    
    # Additional check: ensure the full model includes composition ratios
    full_features = set(full_results['features_used'])
    composition_features = {'O_Fe', 'He_H', 'C_O'}
    assert composition_features.issubset(full_features), \
        "Composition ratios not included in full model features"
    
    print("Regression pipeline integration test passed.")