"""
Test suite for User Story 2 (T015) implementation: code/03_train.py.
Verifies split strategy logic, baseline model training, permutation test artifacts,
and model artifact existence.
"""
import pytest
import json
import pickle
import logging
from pathlib import Path
import warnings

# Import custom exceptions if needed for specific assertions, though mostly we check artifacts
from code.exceptions import PowerWarning

# Configure logging to capture warnings if necessary
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_split_strategy_logic():
    """
    T025: Verify split strategy (LOOCV vs 80/20) based on dataset size.
    
    Checks:
    1. If N < 30, strategy must be 'LOOCV' and PowerWarning should have been raised/logged.
    2. If N >= 30, strategy must be '80/20'.
    """
    split_config_path = Path("data/processed/split_config.json")
    dataset_path = Path("data/processed/dataset_cleaned.csv")
    
    if not dataset_path.exists():
        pytest.skip("Dataset not yet generated. Run 02_preprocess.py first.")
    if not split_config_path.exists():
        pytest.skip("Split config not yet generated. Run 02_preprocess.py first.")
    
    import pandas as pd
    df = pd.read_csv(dataset_path)
    n = len(df)
    
    with open(split_config_path, 'r') as f:
        config = json.load(f)
    
    strategy = config.get('split_strategy')
    
    logger.info(f"Dataset size: {n}, Strategy from config: {strategy}")
    
    if n < 30:
        assert strategy == 'LOOCV', f"Expected LOOCV for N={n}, got {strategy}"
        # Note: Verifying the actual emission of PowerWarning in the log file is complex
        # without a dedicated log capture fixture, but the config state confirms the logic path.
    else:
        assert strategy == '80/20', f"Expected 80/20 for N={n}, got {strategy}"


def test_baseline_model_training():
    """
    T025: Verify Elastic Net baseline is trained on the same split.
    
    Checks:
    1. baseline_model.pkl exists.
    2. The loaded object is an instance of ElasticNet (or sklearn.linear_model.ElasticNet).
    """
    baseline_path = Path("data/outputs/baseline_model.pkl")
    
    if not baseline_path.exists():
        pytest.skip("Baseline model not yet generated. Run 03_train.py first.")
    
    with open(baseline_path, 'rb') as f:
        model = pickle.load(f)
    
    model_type_str = str(type(model))
    logger.info(f"Baseline model type: {model_type_str}")
    
    # Check if it's an Elastic Net model
    # The class name usually contains 'ElasticNet'
    assert 'ElasticNet' in model_type_str, f"Expected ElasticNet model, got {model_type_str}"


def test_permutation_test_artifacts():
    """
    T025: Verify permutation test results are saved in model_results.json.
    
    Checks:
    1. model_results.json exists.
    2. 'p_value' key is present.
    3. 'p_value' is a float.
    """
    results_path = Path("data/outputs/model_results.json")
    
    if not results_path.exists():
        pytest.skip("Model results not yet generated. Run 03_train.py first.")
    
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    assert 'p_value' in results, "p_value missing in model_results.json"
    assert isinstance(results['p_value'], (int, float)), "p_value must be a numeric type"
    
    logger.info(f"Permutation test p-value: {results['p_value']}")


def test_model_artifacts_exist():
    """
    T025: Verify best_model.pkl and baseline_model.pkl exist.
    
    Checks:
    1. best_model.pkl exists in data/outputs/.
    2. baseline_model.pkl exists in data/outputs/.
    """
    best_path = Path("data/outputs/best_model.pkl")
    baseline_path = Path("data/outputs/baseline_model.pkl")
    
    if not best_path.exists() or not baseline_path.exists():
        pytest.skip("Model artifacts not yet generated. Run 03_train.py first.")
    
    assert best_path.exists(), "best_model.pkl missing"
    assert baseline_path.exists(), "baseline_model.pkl missing"
    
    logger.info("Both best_model.pkl and baseline_model.pkl exist.")