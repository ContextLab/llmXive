import pytest
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from cluster_analysis import run_sensitivity_analysis, calculate_cluster_correlations

def create_mock_data():
    """Create a mock dataframe with clustering results."""
    np.random.seed(42)
    n_samples = 100
    data = {
        'bulk_modulus': np.random.rand(n_samples) * 100,
        'shear_modulus': np.random.rand(n_samples) * 100,
        'feature_1': np.random.rand(n_samples),
        'feature_2': np.random.rand(n_samples),
        'feature_3': np.random.rand(n_samples)
    }
    df = pd.DataFrame(data)
    
    # Simulate clustering
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['cluster_id'] = kmeans.fit_predict(df[['feature_1', 'feature_2', 'feature_3']])
    return df

def test_sensitivity_analysis_structure():
    """Test that sensitivity analysis returns correct columns."""
    df = create_mock_data()
    feature_cols = ['feature_1', 'feature_2', 'feature_3']
    
    result = run_sensitivity_analysis(df, feature_cols, k=3)
    
    assert 'cutoff' in result.columns
    assert 'region_size' in result.columns
    assert 'mean_correlation' in result.columns
    assert 'robustness_score' in result.columns
    assert len(result) > 0

def test_robustness_score_calculation():
    """Test that robustness score is calculated as variance of region sizes."""
    df = create_mock_data()
    feature_cols = ['feature_1', 'feature_2', 'feature_3']
    
    result = run_sensitivity_analysis(df, feature_cols, k=3)
    
    # The robustness_score should be constant across rows (it's a single metric for the whole analysis)
    # Or it could be the variance of the sizes.
    # The code calculates variance of cluster_sizes list and assigns it to every row.
    sizes = result['region_size'].values
    expected_variance = np.var(sizes)
    
    # Check if the robustness_score column matches the calculated variance
    # Note: The code assigns the same value to all rows.
    actual_score = result['robustness_score'].iloc[0]
    
    assert np.isclose(actual_score, expected_variance), f"Expected {expected_variance}, got {actual_score}"

def test_empty_result_handling():
    """Test behavior when no clusters meet the cutoff."""
    # Create data where correlations are high (e.g., > 0.95)
    np.random.seed(42)
    n_samples = 50
    data = {
        'bulk_modulus': np.random.rand(n_samples) * 100,
        'shear_modulus': np.random.rand(n_samples) * 100,
        'feature_1': np.random.rand(n_samples),
        'feature_2': np.random.rand(n_samples),
        'feature_3': np.random.rand(n_samples)
    }
    df = pd.DataFrame(data)
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    df['cluster_id'] = kmeans.fit_predict(df[['feature_1', 'feature_2', 'feature_3']])
    
    # Force high correlation
    df['bulk_modulus'] = df['shear_modulus'] * 1.01
    
    feature_cols = ['feature_1', 'feature_2', 'feature_3']
    result = run_sensitivity_analysis(df, feature_cols, k=2)
    
    # Even if correlations are high, the loop should run. 
    # If cutoff is 0.5 and all corr > 0.5, region_size might be 0 for low cutoffs.
    assert len(result) > 0
    # Check that region_size can be 0
    assert result['region_size'].min() >= 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])