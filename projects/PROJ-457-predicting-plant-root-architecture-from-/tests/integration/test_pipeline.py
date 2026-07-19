"""
Integration test for the model training and evaluation pipeline (User Story 2).

This test verifies the end-to-end flow from preprocessed data loading to:
1. Species-stratified train/test split
2. Fitting Linear Mixed-Effects Models (LMM)
3. Fitting Random Forest (RF) baseline
4. Evaluating metrics (R², RMSE, p-values)
5. Calculating R² difference and success criteria

It consumes the output of T016 (preprocessed data) and produces the metrics
required for T029.
"""
import os
import sys
import json
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

import pytest
import pandas as pd
import numpy as np

# Add project root to path to import code modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_config, setup_logging
from preprocessing import apply_log_transformation, apply_zscore_normalization
from modeling import (
    create_species_stratified_split,
    fit_lmm,
    fit_random_forest,
    train_models,
    evaluate_model,
    calculate_r2_delta,
    perform_f_tests_and_pvalues
)

# Setup logging for the test
logger = setup_logging("tests/integration/test_pipeline.log", level=logging.INFO)


@pytest.fixture
def mock_processed_data(tmp_path: Path):
    """
    Creates a realistic mock of the preprocessed dataset expected from T016.
    Since T013/T015 rely on real external data that might fail or be slow,
    and T016 produces specific transformations, we generate a deterministic
    dataset here to test the modeling pipeline logic robustly.
    
    This dataset mimics the schema:
    species, root_length, branching_density, surface_area, phosphorus, nitrogen
    
    It includes multiple species with >20 rows each to satisfy T015 constraints.
    """
    data_path = tmp_path / "processed_data.csv"
    
    np.random.seed(42)
    n_species = 5
    rows_per_species = 30
    total_rows = n_species * rows_per_species
    
    species_list = [f"Species_{i}" for i in range(n_species)]
    
    records = []
    for sp in species_list:
        for _ in range(rows_per_species):
            # Generate correlated root metrics and nutrients
            # Simulate a biological relationship: higher nutrients -> higher root metrics
            nutrient_base = np.random.normal(0, 1) # Z-scored nutrient (simulated)
            
            # Root metrics with some noise and species-specific intercept
            root_length = 2.0 + 0.5 * nutrient_base + np.random.normal(0, 0.2)
            branching_density = 1.5 + 0.3 * nutrient_base + np.random.normal(0, 0.15)
            surface_area = 1.8 + 0.4 * nutrient_base + np.random.normal(0, 0.2)
            
            records.append({
                "species": sp,
                "root_length": root_length,
                "branching_density": branching_density,
                "surface_area": surface_area,
                "phosphorus": nutrient_base, # Using nutrient_base as proxy for z-scored P
                "nitrogen": nutrient_base + np.random.normal(0, 0.1) # Slightly correlated N
            })
    
    df = pd.DataFrame(records)
    df.to_csv(data_path, index=False)
    return data_path


def test_integration_model_pipeline(mock_processed_data: Path):
    """
    End-to-end integration test for the modeling pipeline.
    
    Steps:
    1. Load preprocessed data
    2. Apply log transformation (if not already done in T016, but safe to re-apply or check)
    3. Apply z-score normalization (if not already done)
    4. Split data by species
    5. Train LMM and RF
    6. Evaluate metrics
    7. Verify output structure and values
    """
    logger.info("Starting integration test for modeling pipeline")
    
    # 1. Load Data
    df = pd.read_csv(mock_processed_data)
    assert not df.empty, "Mock data generation failed"
    assert "species" in df.columns, "Missing 'species' column"
    assert "phosphorus" in df.columns, "Missing 'phosphorus' column"
    assert "nitrogen" in df.columns, "Missing 'nitrogen' column"
    logger.info(f"Loaded data with shape {df.shape}")
    
    # 2. Preprocessing (Log Transform & Z-Score)
    # Note: In a real run, T016 would have done this. We do it here to ensure
    # the modeling step receives correctly formatted data for the test.
    # We assume the mock data is already z-scored for nutrients, but we apply log to root metrics.
    # The apply_log_transformation function handles zeros/negatives safely.
    
    root_metrics = ["root_length", "branching_density", "surface_area"]
    df[root_metrics] = apply_log_transformation(df, root_metrics)
    
    nutrient_cols = ["phosphorus", "nitrogen"]
    # Ensure nutrients are z-scored (mock data is, but for robustness we re-normalize if needed)
    # In a strict pipeline, T016 output is consumed. Here we ensure it's valid.
    df[nutrient_cols] = apply_zscore_normalization(df, nutrient_cols)
    
    logger.info("Preprocessing applied successfully")
    
    # 3. Species Stratified Split
    # We use a small test size for speed in integration test
    train_df, test_df = create_species_stratified_split(df, test_size=0.2, random_state=42)
    
    assert len(train_df) > 0, "Training set is empty"
    assert len(test_df) > 0, "Test set is empty"
    assert set(train_df["species"].unique()) == set(test_df["species"].unique()), "Species mismatch between train/test"
    logger.info(f"Split data: Train {len(train_df)}, Test {len(test_df)}")
    
    # 4. Train Models
    # Target variable: root_length (example)
    # Predictors: phosphorus, nitrogen
    target = "root_length"
    features = ["phosphorus", "nitrogen"]
    
    # Train LMM
    lmm_results = fit_lmm(train_df, target, features, random_effect="species")
    assert lmm_results is not None, "LMM fitting failed"
    assert "adjusted_r_squared" in lmm_results, "LMM missing adjusted_r_squared"
    assert "p_values" in lmm_results, "LMM missing p_values"
    logger.info(f"LMM trained: R²={lmm_results['adjusted_r_squared']:.4f}")
    
    # Train RF
    rf_results = fit_random_forest(train_df, target, features, random_state=42, n_estimators=50, max_depth=5)
    assert rf_results is not None, "RF fitting failed"
    assert "adjusted_r_squared" in rf_results, "RF missing adjusted_r_squared"
    logger.info(f"RF trained: R²={rf_results['adjusted_r_squared']:.4f}")
    
    # 5. Evaluate on Test Set
    lmm_test_metrics = evaluate_model(lmm_results, test_df, target, features, model_type="lmm")
    rf_test_metrics = evaluate_model(rf_results, test_df, target, features, model_type="rf")
    
    assert "rmse" in lmm_test_metrics, "LMM test metrics missing RMSE"
    assert "rmse" in rf_test_metrics, "RF test metrics missing RMSE"
    logger.info(f"Test Metrics - LMM RMSE: {lmm_test_metrics['rmse']:.4f}, RF RMSE: {rf_test_metrics['rmse']:.4f}")
    
    # 6. Calculate R² Delta
    r2_delta = calculate_r2_delta(lmm_results["adjusted_r_squared"], rf_results["adjusted_r_squared"])
    assert isinstance(r2_delta, float), "R² delta calculation failed"
    logger.info(f"R² Delta (LMM - RF): {r2_delta:.4f}")
    
    # 7. Perform F-tests and P-values
    f_test_results = perform_f_tests_and_pvalues(lmm_results)
    assert f_test_results is not None, "F-test failed"
    logger.info("F-tests completed")
    
    # 8. Assertions on Output Structure
    # Verify that metrics are reasonable (not NaN, not inf)
    assert np.isfinite(lmm_results["adjusted_r_squared"]), "LMM R² is not finite"
    assert np.isfinite(rf_results["adjusted_r_squared"]), "RF R² is not finite"
    assert np.isfinite(lmm_test_metrics["rmse"]), "LMM RMSE is not finite"
    assert np.isfinite(rf_test_metrics["rmse"]), "RF RMSE is not finite"
    
    # Verify p-values exist
    for coef, p_val in f_test_results["p_values"].items():
        assert 0 <= p_val <= 1, f"P-value for {coef} is out of range: {p_val}"
    
    logger.info("Integration test passed successfully")


if __name__ == "__main__":
    # Run the test directly if executed as a script
    pytest.main([__file__, "-v"])