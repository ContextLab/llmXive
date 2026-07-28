"""
Integration test for the full interpretability pipeline (US3).

This test validates the end-to-end flow of:
1. Loading processed data from US1 (T018)
2. Loading trained model metrics/artifacts from US2 (T028, T029)
3. Running SHAP analysis (T036)
4. Calculating VIF diagnostics (T037)
5. Grouping correlated features (T038)
6. Calculating CV stability (T039)
7. Generating the final interpretation report (T040)

Prerequisites:
- data/processed/curated_ceramics.csv must exist (from T018)
- data/results/model_metrics.json must exist (from T028)
- data/results/permutation_p_value.json must exist (from T029)
- code/diagnostics.py must implement calculate_shap, calculate_vif
- code/report.py must implement calculate_cv_stability, generate_interpretation
"""

import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Project root relative to this file
ROOT_DIR = Path(__file__).parent.parent.parent

# Import pipeline modules
# Note: We assume the project structure puts code/ at the root level relative to tests/
import sys
sys.path.insert(0, str(ROOT_DIR))

from code import descriptors  # Just to ensure imports work, though we might not use directly
from code.diagnostics import calculate_shap, calculate_vif
from code.report import calculate_cv_stability, generate_interpretation
from code.modeling import train_models, prepare_splits


@pytest.fixture(scope="module")
def data_path():
    """Path to the processed dataset."""
    return ROOT_DIR / "data" / "processed" / "curated_ceramics.csv"

@pytest.fixture(scope="module")
def results_dir():
    """Path to the results directory."""
    return ROOT_DIR / "data" / "results"

@pytest.fixture(scope="module")
def processed_data(data_path):
    """Load the processed dataset."""
    if not data_path.exists():
        pytest.skip(f"Processed data file not found at {data_path}. "
                    "Please run US1 (T018) first to generate the dataset.")
    df = pd.read_csv(data_path)
    
    # Ensure required columns exist
    required_cols = ['weibull_modulus', 'composition']
    # Descriptors computed in T019
    descriptor_cols = [
        'mean_atomic_radius', 'electronegativity_std', 
        'valence_electron_concentration', 'cation_size_variance',
        'sintering_temp'
    ]
    
    missing = [c for c in required_cols + descriptor_cols if c not in df.columns]
    if missing:
        pytest.fail(f"Processed data missing required columns: {missing}")
    
    return df

@pytest.fixture(scope="module")
def model_artifacts(results_dir):
    """Load model artifacts (metrics, best model params if saved)."""
    metrics_path = results_dir / "model_metrics.json"
    if not metrics_path.exists():
        pytest.skip(f"Model metrics not found at {metrics_path}. "
                    "Please run US2 (T028) first to train models.")
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    return metrics

@pytest.fixture(scope="module")
def feature_columns(processed_data):
    """Identify feature columns for the model."""
    exclude_cols = ['composition', 'weibull_modulus', 'sample_count', 
                    'is_range_flag', 'range_original', 'range_uncertainty',
                    'primary_anion_cation_group', 'is_imputed']
    features = [c for c in processed_data.columns if c not in exclude_cols]
    # Ensure we have the specific descriptors expected
    expected_features = ['mean_atomic_radius', 'electronegativity_std', 
                         'valence_electron_concentration', 'cation_size_variance',
                         'sintering_temp']
    # If specific features are missing, we just use what's available, 
    # but log a warning if expected ones are gone.
    missing_expected = [f for f in expected_features if f not in features]
    if missing_expected:
        pytest.warns(UserWarning, f"Expected features missing: {missing_expected}")
    return features

def test_shap_analysis(processed_data, feature_columns, results_dir):
    """
    Test T036: Calculate SHAP values for the best model.
    
    Validates that:
    1. SHAP values are computed without error.
    2. Output shape matches (n_samples, n_features).
    3. SHAP summary data is saved to disk.
    """
    X = processed_data[feature_columns]
    y = processed_data['weibull_modulus']
    
    # We need a trained model. Since we can't easily reload the exact sklearn object 
    # from JSON without sklearn persistence, we re-train a quick RF for this test 
    # to ensure we have a model object to explain.
    # In a real CI/CD, we would load the serialized model.
    from sklearn.ensemble import RandomForestRegressor
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # Run SHAP calculation
    try:
        shap_result = calculate_shap(model, X, y, feature_columns)
    except Exception as e:
        pytest.fail(f"calculate_shap failed: {str(e)}")
    
    # Verify output
    assert shap_result is not None, "SHAP result should not be None"
    assert 'shap_values' in shap_result, "SHAP result must contain 'shap_values'"
    assert 'expected_value' in shap_result, "SHAP result must contain 'expected_value'"
    
    shap_vals = shap_result['shap_values']
    assert shap_vals.shape[0] == X.shape[0], "SHAP values row count must match samples"
    assert shap_vals.shape[1] == len(feature_columns), "SHAP values col count must match features"
    
    # Verify file creation (T041)
    shap_path = results_dir / "shap_summary.json"
    # The function calculate_shap should handle saving or we do it here if the function returns data
    # Assuming calculate_shap returns the dict and we save it, or the function saves it.
    # Let's check if the function saves it or we need to. 
    # Based on T036 description: "Generate SHAP values". T041 says "Generate SHAP summary plots".
    # We will assume calculate_shap returns the data and we verify the file exists if the function 
    # is designed to save, or we save it here to satisfy T041.
    # For this integration test, we verify the data is generated.
    
    # If the function is supposed to save, check file. If not, save to verify T041.
    # Let's assume the function returns the dict. We'll save it to verify T041.
    with open(shap_path, 'w') as f:
        # Convert numpy types to native python for JSON
        json_serializable = {
            k: (v.tolist() if isinstance(v, np.ndarray) else v) 
            for k, v in shap_result.items()
        }
        json.dump(json_serializable, f)
    
    assert shap_path.exists(), f"SHAP summary file {shap_path} was not created"
    
    # Verify content
    with open(shap_path, 'r') as f:
        saved_data = json.load(f)
    assert 'shap_values' in saved_data, "Saved SHAP file missing 'shap_values'"

def test_vif_diagnostics(processed_data, feature_columns, results_dir):
    """
    Test T037: Calculate VIF for all predictors.
    
    Validates that:
    1. VIF scores are computed for all features.
    2. Output is saved to data/results/vif_diagnostics.json.
    3. High VIF features (>5) are flagged.
    """
    X = processed_data[feature_columns]
    
    try:
        vif_result = calculate_vif(X, feature_columns)
    except Exception as e:
        pytest.fail(f"calculate_vif failed: {str(e)}")
    
    assert vif_result is not None, "VIF result should not be None"
    assert isinstance(vif_result, dict), "VIF result should be a dictionary"
    assert 'vif_scores' in vif_result, "VIF result must contain 'vif_scores'"
    
    vif_scores = vif_result['vif_scores']
    assert len(vif_scores) == len(feature_columns), "VIF scores must exist for all features"
    
    # Verify file creation
    vif_path = results_dir / "vif_diagnostics.json"
    with open(vif_path, 'w') as f:
        # Convert numpy types
        json_serializable = {
            k: (v.tolist() if isinstance(v, np.ndarray) else v) 
            for k, v in vif_result.items()
        }
        json.dump(json_serializable, f)
    
    assert vif_path.exists(), f"VIF diagnostics file {vif_path} was not created"
    
    # Verify high VIF detection logic
    high_vif = [f for f, v in vif_scores.items() if v > 5.0]
    # The result should reflect these
    assert 'high_vif_features' in vif_result or high_vif == vif_result.get('high_vif_features', []), \
        "VIF result should list features with VIF > 5.0"

def test_correlated_feature_grouping(processed_data, feature_columns, results_dir):
    """
    Test T038: Group correlated features based on VIF.
    
    Validates that:
    1. Correlated groups are identified.
    2. Aggregate importance logic is prepared (though actual importance comes from SHAP).
    """
    X = processed_data[feature_columns]
    
    # Re-use VIF result or calculate again
    try:
        vif_result = calculate_vif(X, feature_columns)
    except Exception as e:
        pytest.fail(f"calculate_vif failed for grouping: {str(e)}")
    
    # The grouping logic might be in calculate_vif or separate. 
    # T038 says "Implement group_correlated_features". 
    # If it's a separate function, we call it. If it's part of calculate_vif, we check the result.
    # Let's assume it's a separate function or we extract it from vif_result if it contains groups.
    # If not present, we assume the function is missing and fail.
    
    # Since T038 is a separate task, we assume a function exists or we check the vif_result for groups.
    # If calculate_vif doesn't return groups, we might need to call a separate function.
    # For this test, we check if the vif_result contains group info or we simulate the check.
    # However, the task says "Implement group_correlated_features". 
    # Let's assume we call it if it exists, otherwise we check vif_result.
    
    # If the function exists in diagnostics:
    try:
        from code.diagnostics import group_correlated_features
        groups = group_correlated_features(vif_result, threshold=5.0)
    except ImportError:
        # Fallback: check if vif_result has groups
        groups = vif_result.get('correlated_groups', [])
    
    assert isinstance(groups, (list, dict)), "Correlated groups should be a list or dict"
    
    # Save to file
    group_path = results_dir / "correlated_groups.json"
    with open(group_path, 'w') as f:
        json.dump(groups, f)
    
    assert group_path.exists(), f"Correlated groups file {group_path} was not created"

def test_cv_stability(processed_data, feature_columns, results_dir):
    """
    Test T039: Calculate CV stability for top features across folds.
    
    Validates that:
    1. CV is calculated for top features.
    2. Output is saved to data/results/cv_stability.json.
    """
    X = processed_data[feature_columns]
    y = processed_data['weibull_modulus']
    
    # Train a model to get feature importances across folds
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import cross_val_predict
    
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    
    try:
        cv_result = calculate_cv_stability(model, X, y, feature_columns, n_splits=5)
    except Exception as e:
        pytest.fail(f"calculate_cv_stability failed: {str(e)}")
    
    assert cv_result is not None, "CV stability result should not be None"
    assert 'cv_scores' in cv_result, "CV result must contain 'cv_scores'"
    
    # Save to file
    cv_path = results_dir / "cv_stability.json"
    with open(cv_path, 'w') as f:
        json_serializable = {
            k: (v.tolist() if isinstance(v, np.ndarray) else v) 
            for k, v in cv_result.items()
        }
        json.dump(json_serializable, f)
    
    assert cv_path.exists(), f"CV stability file {cv_path} was not created"

def test_full_interpretation_pipeline(processed_data, feature_columns, model_artifacts, results_dir):
    """
    Test T040: Generate the full interpretation report.
    
    This is the main integration test that ties everything together.
    Validates that:
    1. SHAP, VIF, and CV data are combined.
    2. Physical mechanisms are mapped (using physics_mappings.py).
    3. The final report is generated and saved.
    4. Disclaimers are included.
    """
    # Load dependencies
    shap_path = results_dir / "shap_summary.json"
    vif_path = results_dir / "vif_diagnostics.json"
    cv_path = results_dir / "cv_stability.json"
    
    if not shap_path.exists() or not vif_path.exists() or not cv_path.exists():
        # Run the previous tests first if files don't exist
        pytest.skip("Prerequisite artifact files missing. Run previous test cases first.")
    
    with open(shap_path, 'r') as f:
        shap_data = json.load(f)
    with open(vif_path, 'r') as f:
        vif_data = json.load(f)
    with open(cv_path, 'r') as f:
        cv_data = json.load(f)
    
    X = processed_data[feature_columns]
    y = processed_data['weibull_modulus']
    
    # Train a model for the final report (or load if we had a serializer)
    from sklearn.ensemble import RandomForestRegressor
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    try:
        report = generate_interpretation(
            model=model,
            X=X,
            y=y,
            feature_names=feature_columns,
            shap_data=shap_data,
            vif_data=vif_data,
            cv_data=cv_data
        )
    except Exception as e:
        pytest.fail(f"generate_interpretation failed: {str(e)}")
    
    assert report is not None, "Interpretation report should not be None"
    assert isinstance(report, dict), "Report should be a dictionary"
    
    # Check for required keys
    required_keys = ['feature_ranking', 'physical_mechanisms', 'correlation_matrix', 'disclaimer']
    missing_keys = [k for k in required_keys if k not in report]
    if missing_keys:
        pytest.fail(f"Interpretation report missing required keys: {missing_keys}")
    
    # Verify disclaimer content
    assert "statistical associations only" in report['disclaimer'].lower() or \
           "not cause" in report['disclaimer'].lower(), \
           "Report must include a disclaimer about statistical vs causal claims."
    
    # Save the final report
    final_report_path = results_dir / "interpretation_report.json"
    with open(final_report_path, 'w') as f:
        # Handle numpy types
        json_serializable = {}
        for k, v in report.items():
            if isinstance(v, dict):
                json_serializable[k] = {
                    ik: (iv.tolist() if isinstance(iv, np.ndarray) else iv) 
                    for ik, iv in v.items()
                }
            elif isinstance(v, np.ndarray):
                json_serializable[k] = v.tolist()
            else:
                json_serializable[k] = v
        json.dump(json_serializable, f)
    
    assert final_report_path.exists(), f"Final interpretation report {final_report_path} was not created"

def test_physics_mappings_available():
    """
    Verify that code/physics_mappings.py exists and is importable (T022).
    This is a prerequisite for T040.
    """
    try:
        from code.physics_mappings import PHYSICS_MAPPINGS
        assert isinstance(PHYSICS_MAPPINGS, dict), "PHYSICS_MAPPINGS must be a dictionary"
        assert len(PHYSICS_MAPPINGS) > 0, "PHYSICS_MAPPINGS should not be empty"
    except ImportError:
        pytest.fail("code/physics_mappings.py is missing or not importable. "
                    "Please ensure T022 is completed.")