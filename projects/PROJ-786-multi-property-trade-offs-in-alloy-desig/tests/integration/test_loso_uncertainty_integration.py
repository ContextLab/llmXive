import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.model_training import run_training_pipeline, calculate_uncertainty, run_loso_cv, prepare_features_targets
from code.utils.logging_config import get_logger

logger = get_logger(__name__)

@pytest.fixture
def sample_data():
    """Create a small sample dataset for testing LOSO-CV and uncertainty integration."""
    # Create a synthetic but realistic-looking dataset for testing
    # We need multiple systems to test LOSO
    n_samples = 100
    n_systems = 10
    samples_per_system = n_samples // n_systems
    
    data = []
    for i in range(n_systems):
        system_name = f"System_{i}"
        for j in range(samples_per_system):
            # Create feature vectors (simulated)
            feat_vector = [np.random.uniform(0, 1) for _ in range(10)]
            # Create target values with some system-specific bias
            bulk_base = 100 + i * 5  # Bulk modulus varies by system
            shear_base = 50 + i * 2  # Shear modulus varies by system
            bulk_modulus = bulk_base + np.random.normal(0, 5)
            shear_modulus = shear_base + np.random.normal(0, 3)
            
            row = {
                'system_name': system_name,
                'bulk_modulus': bulk_modulus,
                'shear_modulus': shear_modulus
            }
            # Add feature columns
            for k, val in enumerate(feat_vector):
                row[f'feat_{k}'] = val
            data.append(row)
    
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_loso_cv_integration(sample_data, temp_output_dir):
    """Test that LOSO-CV runs and produces expected metrics structure."""
    # Prepare data
    target_cols = ['bulk_modulus', 'shear_modulus']
    X, Y = prepare_features_targets(sample_data, target_cols)
    groups = sample_data['system_name'].values
    
    config = {
        'n_estimators': 5,  # Small for speed
        'max_depth': 2,
        'learning_rate': 0.1,
        'n_jobs': 1
    }
    
    # Run LOSO-CV
    results = run_loso_cv(X, Y, groups, config)
    
    # Assertions
    assert 'bulk_modulus' in results
    assert 'shear_modulus' in results
    
    for target in target_cols:
        assert 'mean_r2' in results[target]
        assert 'std_r2' in results[target]
        assert 'sem_r2' in results[target]
        assert 'mean_mse' in results[target]
        assert 'std_mse' in results[target]
        assert 'all_r2_scores' in results[target]
        assert len(results[target]['all_r2_scores']) == len(np.unique(groups))  # One per fold
    
    logger.info(f"LOSO-CV completed. Bulk R2: {results['bulk_modulus']['mean_r2']:.4f}")

def test_uncertainty_linking_to_loso(sample_data, temp_output_dir):
    """Test that uncertainty calculation is properly linked to LOSO-CV results (T022b requirement)."""
    # Prepare data
    target_cols = ['bulk_modulus', 'shear_modulus']
    X, Y = prepare_features_targets(sample_data, target_cols)
    groups = sample_data['system_name'].values
    
    config = {
        'n_estimators': 5,
        'max_depth': 2,
        'learning_rate': 0.1,
        'n_jobs': 1
    }
    
    # Calculate uncertainty
    uncertainties = calculate_uncertainty(X, Y, groups, config)
    
    # Assertions
    assert 'bulk_modulus' in uncertainties
    assert 'shear_modulus' in uncertainties
    
    for target in target_cols:
        assert len(uncertainties[target]) == len(X)
        assert all(u >= 0 for u in uncertainties[target])  # Uncertainty should be non-negative
    
    # Verify that samples from the same system have the same uncertainty
    # (since they were all in the same test fold)
    unique_systems = np.unique(groups)
    for system in unique_systems:
        indices = np.where(groups == system)[0]
        if len(indices) > 0:
            bulk_uncs = [uncertainties['bulk_modulus'][i] for i in indices]
            shear_uncs = [uncertainties['shear_modulus'][i] for i in indices]
            
            # All samples in the same system should have identical uncertainty
            assert np.allclose(bulk_uncs, bulk_uncs[0]), f"Bulk uncertainty varies within system {system}"
            assert np.allclose(shear_uncs, shear_uncs[0]), f"Shear uncertainty varies within system {system}"
    
    logger.info("Uncertainty linking test passed. Samples in same system have consistent uncertainty.")

def test_full_pipeline_integration(sample_data, temp_output_dir):
    """Test the full training pipeline including LOSO-CV, uncertainty, and model saving."""
    # Save sample data to temp location
    data_path = os.path.join(temp_output_dir, "test_encoded.csv")
    sample_data.to_csv(data_path, index=False)
    
    config = {
        'n_estimators': 5,
        'max_depth': 2,
        'learning_rate': 0.1,
        'n_jobs': 1
    }
    
    # Run full pipeline
    metrics, models, uncertainties = run_training_pipeline(data_path, temp_output_dir, config)
    
    # Assertions
    assert 'bulk_modulus' in metrics
    assert 'shear_modulus' in metrics
    
    # Check that uncertainty is integrated into metrics (T022b requirement)
    for target in ['bulk_modulus', 'shear_modulus']:
        assert 'mean_uncertainty' in metrics[target]
        assert 'max_uncertainty' in metrics[target]
        assert 'uncertainty_samples' in metrics[target]
    
    # Check models were saved
    assert 'bulk_modulus' in models
    assert 'shear_modulus' in models
    
    # Check files were created
    assert os.path.exists(os.path.join(temp_output_dir, "training_metrics.json"))
    assert os.path.exists(os.path.join(temp_output_dir, "uncertainties.csv"))
    assert os.path.exists(os.path.join(temp_output_dir, "models", "bulk_modulus_model.pkl"))
    assert os.path.exists(os.path.join(temp_output_dir, "models", "shear_modulus_model.pkl"))
    
    logger.info("Full pipeline integration test passed.")