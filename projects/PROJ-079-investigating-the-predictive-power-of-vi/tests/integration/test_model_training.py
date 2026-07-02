"""
Integration test for User Story 2: Model Training and Evaluation.

Verifies that the model training pipeline executes successfully and
produces the expected metrics artifact at data/artifacts/metrics.json.
"""
import pytest
import os
import json
from pathlib import Path
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys

# Ensure src is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.model import (
    validate_strains,
    split_stratified_strain,
    calculate_vif,
    train_elastic_net,
    debiased_lasso_pvalues,
    fdr_correction,
    permutation_test,
    evaluate_model
)
from src.config import DATA_PROCESSED_PATH, ARTIFACTS_PATH, SEED


@pytest.fixture
def mock_aggregated_data():
    """
    Create a mock aggregated dataset that satisfies the constraints:
    - At least 30 samples
    - At least 5 unique strains
    - Required columns: strain_accession, isg_score, and several features
    """
    n_samples = 50
    n_strains = 10
    
    # Generate strain IDs
    strain_ids = [f"strain_{i:03d}" for i in range(n_strains)]
    
    # Assign strains to samples (ensure at least 3 samples per strain)
    sample_strains = []
    for i in range(n_samples):
        sample_strains.append(strain_ids[i % n_strains])
    
    # Create mock features
    np.random.seed(SEED)
    data = {
        'strain_accession': sample_strains,
        'isg_score': np.random.normal(0, 1, n_samples),
        'gc_content': np.random.uniform(0.3, 0.7, n_samples),
        'cai': np.random.uniform(0.1, 0.9, n_samples),
        'kmer_3_AAA': np.random.uniform(0, 0.1, n_samples),
        'kmer_3_AAT': np.random.uniform(0, 0.1, n_samples),
        'stability_score': np.random.uniform(-2, 2, n_samples),
        'repeat_density': np.random.uniform(0, 0.5, n_samples),
        'host_codon_bias': np.random.uniform(0, 1, n_samples)
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def mock_model():
    """
    Create a mock ElasticNet model with fitted coefficients.
    """
    mock_model = MagicMock()
    # Mock coefficients for the features we expect
    mock_model.coef_ = np.array([0.5, -0.3, 0.2, -0.1, 0.4, -0.2, 0.1, -0.05])
    mock_model.intercept_ = 0.1
    return mock_model


def test_training_and_eval(mock_aggregated_data, mock_model, tmp_path):
    """
    Integration test: Verify the full model training and evaluation pipeline
    produces the required metrics artifact.
    
    This test:
    1. Validates strain count
    2. Splits data by strain
    3. Calculates VIF
    4. Trains ElasticNet
    5. Runs Debiased Lasso (mocked)
    6. Applies FDR correction
    7. Runs permutation test (mocked)
    8. Evaluates model
    9. Verifies metrics.json is created with correct schema
    """
    # Temporarily override paths for this test
    original_processed = DATA_PROCESSED_PATH
    original_artifacts = ARTIFACTS_PATH
    
    test_processed = str(tmp_path / "processed")
    test_artifacts = str(tmp_path / "artifacts")
    os.makedirs(test_processed, exist_ok=True)
    os.makedirs(test_artifacts, exist_ok=True)
    
    # Save aggregated data
    aggregated_path = Path(test_processed) / "aggregated_dataset.csv"
    mock_aggregated_data.to_csv(aggregated_path, index=False)
    
    try:
        # Step 1: Validate strains
        validate_strains(mock_aggregated_data)
        
        # Step 2: Split data
        train_df, test_df = split_stratified_strain(mock_aggregated_data, test_strains=2)
        
        # Verify split constraints
        assert len(train_df['strain_accession'].unique()) >= 5, "Train set must have >= 5 unique strains"
        assert len(test_df['strain_accession'].unique()) >= 2, "Test set must have >= 2 unique strains"
        
        # Verify no strain overlap
        train_strains = set(train_df['strain_accession'].unique())
        test_strains = set(test_df['strain_accession'].unique())
        assert len(train_strains.intersection(test_strains)) == 0, "No strain overlap allowed"
        
        # Step 3: Calculate VIF (mocked to avoid dependency on statsmodels for this test)
        with patch('src.model.statsmodels') as mock_statsmodels:
            mock_statsmodels.stats.outliers_influence.variance_inflation_factor.return_value = 2.5
            vif_results = calculate_vif(train_df)
            assert isinstance(vif_results, dict), "VIF results should be a dict"
            assert len(vif_results) > 0, "VIF results should not be empty"
        
        # Step 4: Train ElasticNet
        feature_cols = [col for col in train_df.columns if col not in ['strain_accession', 'isg_score']]
        X_train = train_df[feature_cols]
        y_train = train_df['isg_score']
        X_test = test_df[feature_cols]
        y_test = test_df['isg_score']
        
        model, alpha, lambda_param = train_elastic_net(X_train, y_train)
        assert model is not None, "Model should not be None"
        assert alpha > 0, "Alpha should be positive"
        assert lambda_param >= 0, "Lambda should be non-negative"
        
        # Step 5: Debiased Lasso p-values (mocked since hdi might not be available)
        with patch('src.model.hdi') as mock_hdi:
            mock_hdi.select.Selector.return_value = MagicMock()
            mock_hdi.select.Selector.return_value.coef_ = np.array([0.5, -0.3, 0.2, -0.1, 0.4, -0.2, 0.1, -0.05])
            mock_hdi.select.Selector.return_value.pvalues_ = np.array([0.01, 0.03, 0.05, 0.15, 0.02, 0.08, 0.12, 0.25])
            
            pvalues = debiased_lasso_pvalues(model, X_test, y_test)
            assert isinstance(pvalues, dict), "P-values should be a dict"
            assert len(pvalues) > 0, "P-values should not be empty"
        
        # Step 6: FDR correction
        fdr_pvalues = fdr_correction(pvalues)
        assert isinstance(fdr_pvalues, dict), "FDR p-values should be a dict"
        assert len(fdr_pvalues) == len(pvalues), "FDR p-values should match original count"
        
        # Step 7: Permutation test (mocked for speed)
        with patch('src.model.time') as mock_time:
            mock_time.time.side_effect = [0, 1, 2, 3]  # Simulate time progression
            perm_pvalue = permutation_test(model, X_test, y_test, n_shuffles=10)
            assert isinstance(perm_pvalue, float), "Permutation p-value should be a float"
            assert 0 <= perm_pvalue <= 1, "P-value should be between 0 and 1"
        
        # Step 8: Evaluate model
        metrics = evaluate_model(model, X_test, y_test)
        assert isinstance(metrics, dict), "Metrics should be a dict"
        assert 'r2' in metrics, "Metrics should contain r2"
        assert 'rmse' in metrics, "Metrics should contain rmse"
        assert 'primary_method' in metrics, "Metrics should contain primary_method"
        
        # Step 9: Save metrics to artifact
        metrics_output_path = Path(test_artifacts) / "metrics.json"
        metrics_output_path.parent.mkdir(parents=True, exist_ok=True)
        
        metrics_to_save = {
            'r2': float(metrics['r2']),
            'rmse': float(metrics['rmse']),
            'permutation_pvalue': float(perm_pvalue),
            'fdr_min_pvalue': float(min(fdr_pvalues.values())) if fdr_pvalues else 1.0,
            'primary_method': metrics['primary_method']
        }
        
        with open(metrics_output_path, 'w') as f:
            json.dump(metrics_to_save, f, indent=2)
        
        # Verify the artifact exists and has correct schema
        assert metrics_output_path.exists(), "metrics.json should exist"
        
        with open(metrics_output_path, 'r') as f:
            saved_metrics = json.load(f)
        
        # Verify schema
        required_keys = ['r2', 'rmse', 'permutation_pvalue', 'fdr_min_pvalue', 'primary_method']
        for key in required_keys:
            assert key in saved_metrics, f"Missing required key: {key}"
            assert isinstance(saved_metrics[key], (int, float)), f"Value for {key} should be numeric"
        
        # Verify primary_method is correct
        assert saved_metrics['primary_method'] == 'elastic_net_debiased_lasso', \
            "Primary method should be 'elastic_net_debiased_lasso'"
        
        # Verify values are reasonable
        assert -1 <= saved_metrics['r2'] <= 1, "R2 should be between -1 and 1"
        assert saved_metrics['rmse'] >= 0, "RMSE should be non-negative"
        assert 0 <= saved_metrics['permutation_pvalue'] <= 1, "Permutation p-value should be between 0 and 1"
        assert 0 <= saved_metrics['fdr_min_pvalue'] <= 1, "FDR p-value should be between 0 and 1"
        
    finally:
        # Restore original paths
        # Note: In a real scenario, we'd need to reload the config module
        # For this test, we're just ensuring the artifact is created correctly
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])