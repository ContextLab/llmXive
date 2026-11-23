"""
Unit test for TreeSHAP calculation on a small dataset.

This test verifies that the SHAP analysis module can successfully
compute TreeSHAP values for a trained Random Forest model on a
small, synthetic subset of the real data (to avoid API dependencies
during unit testing).

Note: The model is trained on a small, fixed-seed sample of the
real data (if available) or a minimal synthetic dataset that
mimics the structure of the real data. This ensures the test
runs quickly and deterministically without requiring external
API calls or large datasets.
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from modeling.train import train_random_forest_cv
from modeling.features import prepare_modeling_features
from utils.logging import get_logger
from config import CONFIG

logger = get_logger(__name__)


def create_small_test_dataset():
    """
    Create a small, deterministic dataset for unit testing.
    
    This mimics the structure of the real merged dataset but with
    a small number of rows to ensure fast execution.
    """
    np.random.seed(42)  # Fixed seed for reproducibility
    n_samples = 20  # Small dataset for unit test

    data = {
        'composition': ['Fe' * n_samples],  # Placeholder, will be parsed
        'shear_modulus_GPa': np.random.uniform(70, 90, n_samples),
        'bulk_modulus_GPa': np.random.uniform(150, 170, n_samples),
        'youngs_modulus_GPa': np.random.uniform(200, 220, n_samples),
        'poissons_ratio': np.random.uniform(0.25, 0.35, n_samples),
        'yield_strength_MPa': np.random.uniform(200, 600, n_samples),
    }

    # Create a DataFrame with proper structure
    df = pd.DataFrame(data)
    
    # Add element columns (simplified for test)
    elements = ['Fe', 'C', 'Mn', 'Cr', 'Ni']
    for elem in elements:
        df[f'fraction_{elem}'] = np.random.uniform(0, 0.1, n_samples)
    
    # Normalize fractions to sum to 1
    fraction_cols = [f'fraction_{elem}' for elem in elements]
    df[fraction_cols] = df[fraction_cols].div(df[fraction_cols].sum(axis=1), axis=0)

    return df


def test_shap_calculation_on_small_dataset():
    """
    Test that TreeSHAP values can be calculated on a small dataset.
    
    This test:
    1. Creates a small test dataset
    2. Trains a Random Forest model
    3. Calculates TreeSHAP values
    4. Verifies the output structure and dimensions
    """
    # Create small test dataset
    logger.info("Creating small test dataset for SHAP unit test")
    df = create_small_test_dataset()
    
    # Prepare features
    logger.info("Preparing features for modeling")
    feature_cols = [col for col in df.columns if col.startswith('fraction_') or col.endswith('_GPa') or col.endswith('_ratio')]
    target_col = 'yield_strength_MPa'
    
    X = df[feature_cols]
    y = df[target_col]
    
    # Train a model (using a small number of trees for speed)
    logger.info("Training Random Forest model for SHAP test")
    model, feature_names, _ = train_random_forest_cv(
        X, y, 
        n_estimators=10,  # Small number for fast testing
        cv_folds=3,
        random_state=42
    )
    
    # Verify model was trained
    assert model is not None, "Model training failed"
    assert hasattr(model, 'estimators_'), "Model does not have estimators"
    
    # Calculate TreeSHAP values
    try:
        import shap
        logger.info("Calculating TreeSHAP values")
        
        # Create a SHAP explainer for the trained model
        explainer = shap.TreeExplainer(model)
        
        # Calculate SHAP values for the test data
        shap_values = explainer.shap_values(X)
        
        # Verify output structure
        assert shap_values is not None, "SHAP values calculation failed"
        
        # Check dimensions
        if isinstance(shap_values, list):
            # For multi-output models, shap_values is a list
            assert len(shap_values) > 0, "SHAP values list is empty"
            # For regression, it might be a single array or list with one array
            if len(shap_values) == 1:
                shap_array = shap_values[0]
            else:
                shap_array = np.array(shap_values)
        else:
            shap_array = shap_values
        
        assert isinstance(shap_array, np.ndarray), "SHAP values should be a numpy array"
        assert shap_array.shape[0] == X.shape[0], f"SHAP values row count ({shap_array.shape[0]}) doesn't match input ({X.shape[0]})"
        assert shap_array.shape[1] == X.shape[1], f"SHAP values feature count ({shap_array.shape[1]}) doesn't match input ({X.shape[1]})"
        
        logger.info(f"SHAP values calculated successfully: shape {shap_array.shape}")
        
        # Test that we can compute summary statistics
        mean_shap = np.abs(shap_array).mean(axis=0)
        assert len(mean_shap) == X.shape[1], "Mean SHAP values length mismatch"
        
        logger.info("SHAP summary statistics computed successfully")
        
    except ImportError:
        pytest.skip("SHAP library not installed, skipping SHAP calculation test")
    except Exception as e:
        pytest.fail(f"SHAP calculation failed: {str(e)}")


def test_shap_explainer_initialization():
    """
    Test that the SHAP explainer can be initialized with a trained model.
    """
    # Create small dataset
    df = create_small_test_dataset()
    
    feature_cols = [col for col in df.columns if col.startswith('fraction_') or col.endswith('_GPa') or col.endswith('_ratio')]
    target_col = 'yield_strength_MPa'
    
    X = df[feature_cols]
    y = df[target_col]
    
    # Train a minimal model
    model, _, _ = train_random_forest_cv(
        X, y, 
        n_estimators=5,
        cv_folds=2,
        random_state=42
    )
    
    try:
        import shap
        
        # Test explainer initialization
        explainer = shap.TreeExplainer(model)
        assert explainer is not None, "Explainer initialization failed"
        
        # Test that we can get expected values
        expected_values = explainer.expected_value
        assert expected_values is not None, "Expected values not computed"
        
    except ImportError:
        pytest.skip("SHAP library not installed")
    except Exception as e:
        pytest.fail(f"SHAP explainer test failed: {str(e)}")


def test_shap_values_for_single_sample():
    """
    Test SHAP calculation on a single sample to verify per-feature contributions.
    """
    # Create small dataset
    df = create_small_test_dataset()
    
    feature_cols = [col for col in df.columns if col.startswith('fraction_') or col.endswith('_GPa') or col.endswith('_ratio')]
    target_col = 'yield_strength_MPa'
    
    X = df[feature_cols]
    y = df[target_col]
    
    # Train model
    model, _, _ = train_random_forest_cv(
        X, y, 
        n_estimators=5,
        cv_folds=2,
        random_state=42
    )
    
    try:
        import shap
        
        # Test on a single sample
        single_sample = X.iloc[[0]]
        
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(single_sample)
        
        if isinstance(shap_values, list):
            if len(shap_values) == 1:
                shap_array = shap_values[0]
            else:
                shap_array = np.array(shap_values)
        else:
            shap_array = shap_values
        
        assert shap_array.shape[0] == 1, "Single sample SHAP should have 1 row"
        assert shap_array.shape[1] == X.shape[1], "Single sample SHAP should have all features"
        
        # Verify that SHAP values are finite numbers
        assert np.all(np.isfinite(shap_array)), "SHAP values contain non-finite numbers"
        
    except ImportError:
        pytest.skip("SHAP library not installed")
    except Exception as e:
        pytest.fail(f"Single sample SHAP test failed: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])