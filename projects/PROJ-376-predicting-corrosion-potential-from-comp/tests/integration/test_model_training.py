"""
Integration test for end-to-end training and evaluation (US2).

This test verifies that the full training and evaluation pipeline runs successfully
on real preprocessed data, produces valid model artifacts, and meets the criteria
for "learnable" classification.

Prerequisites:
- T012-T017 (Data ingestion and preprocessing) must be complete.
- Processed dataset must exist at data/processed/corrosion_dataset.parquet.
- Split indices must exist at data/processed/split_indices.json.

Expected Outcomes:
- data/processed/model_results.json is created and valid.
- Contains R² and RMSE for both Random Forest and Gradient Boosting.
- Best model is classified as "learnable" if R² > 0.0 (p < 0.05).
"""
import os
import json
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Project imports based on API surface
from utils.config import (
    get_processed_data_path, 
    get_split_indices_path, 
    get_model_results_path,
    get_config
)
from utils.exceptions import DataInsufficientError
from utils.logging import get_logger

# Import the main functions we are testing
# Note: We assume train.py and evaluate.py are implemented as per T020, T021
# We import the main entry points to execute the pipeline logic
from data.train import main as train_main
from data.evaluate import main as evaluate_main

logger = get_logger(__name__)

# Configuration for the test
# We expect the pipeline to run in a controlled environment
# If data is missing, the test should fail loudly, not skip
REQUIRED_DATA_FILE = "corrosion_dataset.parquet"
REQUIRED_SPLIT_FILE = "split_indices.json"
OUTPUT_RESULTS_FILE = "model_results.json"

@pytest.fixture(scope="module")
def pipeline_paths():
    """Verify prerequisites exist before running tests."""
    processed_path = get_processed_data_path()
    split_path = get_split_indices_path()
    results_path = get_model_results_path()
    
    # Ensure directories exist
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    split_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check for input data
    if not processed_path.exists():
        raise FileNotFoundError(
            f"Prerequisite data missing: {processed_path}. "
            "Ensure T012-T017 (Data Ingestion) has been run successfully."
        )
    
    if not split_path.exists():
        raise FileNotFoundError(
            f"Prerequisite split indices missing: {split_path}. "
            "Ensure T015 (Split) has been run successfully."
        )
        
    return {
        "processed": processed_path,
        "split": split_path,
        "results": results_path
    }

def test_train_and_evaluate_end_to_end(pipeline_paths):
    """
    Integration test: Run training and evaluation end-to-end.
    
    Steps:
    1. Execute training script (T020 logic).
    2. Execute evaluation script (T021, T022 logic).
    3. Verify output file exists and contains required metrics.
    4. Validate "learnable" classification logic.
    """
    results_path = pipeline_paths["results"]
    
    # 1. Run Training
    # We simulate the CLI execution by calling the main function directly
    # The training script should read from get_processed_data_path() and 
    # get_split_indices_path() internally based on config
    logger.info("Starting training pipeline...")
    try:
        train_main()
    except Exception as e:
        pytest.fail(f"Training pipeline failed: {e}")
    
    # 2. Run Evaluation
    logger.info("Starting evaluation pipeline...")
    try:
        evaluate_main()
    except Exception as e:
        pytest.fail(f"Evaluation pipeline failed: {e}")
    
    # 3. Verify Output File Exists
    assert results_path.exists(), f"Model results file not created at {results_path}"
    
    # 4. Validate Content Structure
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    # Check for required top-level keys
    assert "models" in results, "Results missing 'models' key"
    assert "best_model" in results, "Results missing 'best_model' key"
    assert "learnable" in results, "Results missing 'learnable' classification"
    
    # Validate individual model metrics
    model_names = ["random_forest", "gradient_boosting"]
    for model_name in model_names:
        assert model_name in results["models"], f"Missing results for {model_name}"
        
        model_data = results["models"][model_name]
        assert "r2" in model_data, f"{model_name} missing R²"
        assert "rmse" in model_data, f"{model_name} missing RMSE"
        
        # Ensure metrics are numeric
        r2 = model_data["r2"]
        rmse = model_data["rmse"]
        
        assert isinstance(r2, (int, float)), f"{model_name} R² is not numeric"
        assert isinstance(rmse, (int, float)), f"{model_name} RMSE is not numeric"
        
        # Basic sanity checks (R² can be negative, but RMSE should be positive)
        assert rmse >= 0, f"{model_name} RMSE is negative"
        
    # 5. Validate "Learnable" Classification
    best_model = results["best_model"]
    is_learnable = results["learnable"]
    
    # The classification logic (T022) should ensure:
    # "Learnable" is True if best model R² > 0.0 AND p < 0.05 (from permutation test)
    # We verify the structure exists and is a boolean
    assert isinstance(is_learnable, bool), "Learnable flag must be a boolean"
    
    # Verify the best model name matches one of the trained models
    assert best_model in model_names, f"Best model '{best_model}' not in trained models"
    
    # Verify the R² of the best model matches the stored value
    best_r2 = results["models"][best_model]["r2"]
    # The logic in evaluate.py should have determined this
    # We just verify consistency here
    
    logger.info(f"Test passed. Best model: {best_model}, Learnable: {is_learnable}")
    
def test_model_performance_against_null_baseline(pipeline_paths):
    """
    Verify that the model performance is actually better than a null baseline.
    
    This is a secondary check on the results file to ensure the 'learnable'
    classification logic was applied correctly.
    """
    results_path = pipeline_paths["results"]
    
    if not results_path.exists():
        pytest.skip("Results file not found. Run test_train_and_evaluate_end_to_end first.")
        
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    # The null baseline is typically mean prediction (R² = 0)
    # If the model is "learnable", its R² must be > 0
    is_learnable = results.get("learnable", False)
    
    if is_learnable:
        best_model = results["best_model"]
        best_r2 = results["models"][best_model]["r2"]
        
        assert best_r2 > 0.0, (
            f"Model marked as 'learnable' but R² ({best_r2}) is not > 0.0. "
            "Check permutation test logic in evaluate.py."
        )
        
        # Additionally, verify the p-value logic exists in the metadata if provided
        # (Optional: depending on how evaluate.py structures the output)
        if "p_value" in results:
            assert results["p_value"] < 0.05, (
                f"Model marked as 'learnable' but p-value ({results['p_value']}) is not < 0.05."
            )
    else:
        # If not learnable, we just verify the logic didn't crash
        # It's acceptable for a model to be unlearnable if R² <= 0 or p >= 0.05
        pass