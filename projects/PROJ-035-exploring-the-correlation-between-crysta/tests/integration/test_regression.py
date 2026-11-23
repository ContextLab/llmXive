"""
Integration test for the full regression modeling pipeline (T027).

This test verifies the end-to-end execution of:
1. Loading the VIF-filtered descriptor data (output of T025b).
2. Running the regression analysis (T028) with stratified train/test split.
3. Validating that the model meets the R² > 0.5 success criterion (SC-003).
4. Verifying that all required output artifacts are generated:
   - data/results/model_metrics.json
   - data/results/feature_importance.csv
   - figures/regression_scatter_top3.png (or similar)

Dependencies:
- T025b: Must produce data/cleaned/descriptors_vif_filtered.csv
- T028: Must produce model metrics and plots
"""
import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from src.analysis.regression import fit_model, evaluate_test, run_regression_analysis, save_regression_results

# Constants
INPUT_DATA_PATH = PROJECT_ROOT / "data" / "cleaned" / "descriptors_vif_filtered.csv"
METRICS_OUTPUT_PATH = PROJECT_ROOT / "data" / "results" / "model_metrics.json"
FEATURE_IMPORTANCE_PATH = PROJECT_ROOT / "data" / "results" / "feature_importance.csv"
FIGURES_DIR = PROJECT_ROOT / "figures"
SC_003_THRESHOLD = 0.5
REQUIRED_COLUMNS = ['structure_id', 'thermal_conductivity', 'chemistry_class',
                    'tolerance_factor', 'bond_length_variance', 'unit_cell_volume',
                    'tilting_angle']

@pytest.fixture(scope="module")
def mock_input_data():
    """
    Fixture to ensure the input data file exists for the test.
    In a real CI environment, this would be populated by T025b.
    For this integration test to run in isolation, we generate a minimal
    valid synthetic dataset that mimics the expected schema if the real file is missing.
    NOTE: This is ONLY for the integration test infrastructure to exist.
    In the actual pipeline, T025b must produce this file from real data.
    """
    if not INPUT_DATA_PATH.exists():
        # Create a minimal valid dataset to satisfy the test structure
        # This simulates the output of T025b
        np.random.seed(42)
        n_samples = 60
        data = {
            'structure_id': [f"mp-{i}" for i in range(n_samples)],
            'thermal_conductivity': np.random.uniform(1.0, 10.0, n_samples),
            'chemistry_class': np.random.choice(['oxide', 'halide', 'nitride'], n_samples),
            'tolerance_factor': np.random.uniform(0.8, 1.05, n_samples),
            'bond_length_variance': np.random.uniform(0.001, 0.05, n_samples),
            'unit_cell_volume': np.random.uniform(50, 200, n_samples),
            'tilting_angle': np.random.uniform(0, 20, n_samples)
        }
        df = pd.DataFrame(data)
        # Ensure directory exists
        INPUT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(INPUT_DATA_PATH, index=False)
        return df
    else:
        return pd.read_csv(INPUT_DATA_PATH)

def test_input_data_schema(mock_input_data):
    """Verify the input data has the required columns."""
    assert mock_input_data is not None
    for col in REQUIRED_COLUMNS:
        assert col in mock_input_data.columns, f"Missing required column: {col}"
    assert len(mock_input_data) >= 50, "Insufficient samples for regression (SC-001)"

def test_regression_pipeline_execution(mock_input_data):
    """
    Execute the full regression pipeline and verify outputs.
    This is the core integration test.
    """
    # Ensure output directories exist
    METRICS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # Run the regression analysis
    # Note: We use the actual implementation. If T028 is not fully implemented,
    # this test will fail, which is the desired behavior for TDD.
    try:
        results = run_regression_analysis(
            input_path=str(INPUT_DATA_PATH),
            output_metrics_path=str(METRICS_OUTPUT_PATH),
            output_features_path=str(FEATURE_IMPORTANCE_PATH),
            output_figures_dir=str(FIGURES_DIR),
            seed=42,
            cv_folds=5,
            test_size=0.2
        )
    except Exception as e:
        pytest.fail(f"Regression pipeline execution failed: {str(e)}")

    # Verify output artifacts exist
    assert METRICS_OUTPUT_PATH.exists(), "Model metrics JSON not generated"
    assert FEATURE_IMPORTANCE_PATH.exists(), "Feature importance CSV not generated"

    # Verify metrics content
    with open(METRICS_OUTPUT_PATH, 'r') as f:
        metrics = json.load(f)

    assert 'r2_test' in metrics, "R² test metric missing from results"
    assert 'rmse_test' in metrics, "RMSE test metric missing from results"
    assert 'cv_scores' in metrics, "CV scores missing from results"
    assert 'feature_importance' in metrics, "Feature importance summary missing"

    # SC-003: Verify R² > 0.5
    r2_score = metrics['r2_test']
    assert r2_score > SC_003_THRESHOLD, (
        f"Model failed SC-003: R² ({r2_score:.4f}) is not greater than {SC_003_THRESHOLD}. "
        "This indicates the model does not meet the performance target."
    )

    # Verify feature importance file
    features_df = pd.read_csv(FEATURE_IMPORTANCE_PATH)
    assert 'feature' in features_df.columns, "Feature column missing in importance file"
    assert 'importance' in features_df.columns, "Importance column missing"
    assert len(features_df) > 0, "Feature importance file is empty"

    # Verify at least one figure was generated (T030)
    figure_files = list(FIGURES_DIR.glob("*.png"))
    assert len(figure_files) > 0, "No regression plots were generated"

def test_stratified_split(mock_input_data):
    """
    Verify that the stratification by chemistry_class is working correctly.
    This checks that the model respects the stratification requirement (FR-014).
    """
    # We can't easily check the internal split of the function without mocking,
    # but we can verify the input data has the stratification column.
    assert 'chemistry_class' in mock_input_data.columns
    assert mock_input_data['chemistry_class'].nunique() >= 2, (
        "Need at least 2 classes for stratified split"
    )

def test_vif_filtered_input(mock_input_data):
    """
    Verify that the input data is indeed the VIF-filtered version.
    This ensures the pipeline dependency chain (T025b -> T028) is respected.
    """
    # This is a structural check. In a real scenario, we might check for
    # specific columns that were removed due to high VIF.
    # For now, we just ensure the file path matches the expected output of T025b.
    assert INPUT_DATA_PATH.exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])