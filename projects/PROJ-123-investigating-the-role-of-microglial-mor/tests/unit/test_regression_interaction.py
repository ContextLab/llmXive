import pytest
import pandas as pd
import numpy as np
from code.analysis import run_regression_with_interaction, prepare_analysis_dataset
from code.synthetic_data import generate_synthetic_dataset
from code.config import set_seed

@pytest.fixture
def synthetic_data_with_interaction():
    """Generate synthetic data with a known interaction effect."""
    set_seed(42)
    # Create a dataset where the effect of pathology depends on brain region
    n = 200
    df = pd.DataFrame({
        'subject_id': range(n),
        'brain_region': np.random.choice(['Hippocampus', 'Prefrontal Cortex'], n),
        'pathology_status': np.random.choice(['Normal', 'Early AD'], n),
        'branch_points': np.random.normal(10, 2, n),
        'total_length': np.random.normal(50, 10, n),
        'soma_area': np.random.normal(20, 5, n),
        'sholl_intersections': np.random.normal(5, 1, n),
        'cognitive_score': np.random.normal(100, 15, n),
        'amyloid_beta_load': np.random.normal(0.5, 0.2, n)
    })
    
    # Inject a strong interaction effect into cognitive_score
    # If Hippocampus AND Early AD -> Score drops significantly more than additive
    mask = (df['brain_region'] == 'Hippocampus') & (df['pathology_status'] == 'Early AD')
    df.loc[mask, 'cognitive_score'] -= 30  # Strong interaction penalty
    
    return df

def test_regression_identifies_interaction(synthetic_data_with_interaction):
    """Verify the regression model detects the injected interaction term (p < 0.05)."""
    df = synthetic_data_with_interaction
    
    # Prepare data
    df = prepare_analysis_dataset(df)
    
    # Run regression
    results = run_regression_with_interaction(df)
    
    # Check that interaction terms exist
    assert 'interaction_terms' in results
    assert len(results['interaction_terms']) > 0, "No interaction terms found in model."
    
    # Check significance of at least one interaction term
    # The interaction term is typically named "C(pathology_status)[T.Early AD]:C(brain_region)[T.Hippocampus]"
    # or similar. We look for any term with ':' and p < 0.05.
    significant_interaction = False
    for term, p_val in results['interaction_terms'].items():
        if p_val < 0.05:
            significant_interaction = True
            break
    
    assert significant_interaction, "Failed to detect significant interaction effect (p < 0.05)."
    
    # Verify R-squared is reasonable (model explains variance)
    assert results['r_squared'] > 0.1, "Model R-squared is too low, suggesting poor fit."

def test_regression_handles_categorical_encoding():
    """Verify that categorical variables are correctly encoded in the formula."""
    df = pd.DataFrame({
        'brain_region': ['Hippocampus', 'Prefrontal Cortex', 'Hippocampus'],
        'pathology_status': ['Normal', 'Early AD', 'Normal'],
        'branch_points': [10, 12, 9],
        'total_length': [50, 55, 48],
        'soma_area': [20, 22, 19],
        'sholl_intersections': [5, 6, 4],
        'cognitive_score': [100, 80, 105]
    })
    
    df = prepare_analysis_dataset(df)
    results = run_regression_with_interaction(df)
    
    assert 'formula' in results
    assert 'C(pathology_status)' in results['formula']
    assert 'C(brain_region)' in results['formula']
    assert '*' in results['formula'] # Interaction operator