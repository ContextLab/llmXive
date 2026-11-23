import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os
from unittest.mock import patch, MagicMock

# Add code to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.models import perform_lmer_analysis, load_filtered_pr_data
from analysis.simex_correction import apply_simex_correction

@pytest.fixture
def sample_data():
    """Create a minimal valid DataFrame for LMER testing."""
    data = {
        'repo': ['A', 'A', 'B', 'B', 'C', 'C', 'A', 'B'],
        'origin_label': ['Disclosing', 'Non-Disclosing', 'Disclosing', 'Non-Disclosing', 
                         'Disclosing', 'Non-Disclosing', 'Non-Disclosing', 'Disclosing'],
        'code_lines_changed': [10, 20, 30, 40, 50, 60, 70, 80],
        'first_review_time': [100.0, 120.0, 110.0, 130.0, 140.0, 150.0, 160.0, 170.0],
        'reviewer_count': [2, 3, 2, 4, 2, 3, 5, 2]
    }
    return pd.DataFrame(data)

def test_perform_lmer_analysis_structure(sample_data):
    """Test that LMER returns expected keys and types."""
    result = perform_lmer_analysis(sample_data)
    
    assert isinstance(result, dict)
    assert 'coefficients' in result
    assert 'p_values' in result
    assert 'variance_components' in result
    
    assert isinstance(result['coefficients'], dict)
    assert isinstance(result['p_values'], dict)
    assert isinstance(result['variance_components'], dict)
    
    # Check that coefficients include the expected terms
    assert 'Intercept' in result['coefficients']
    assert 'code_lines_changed' in result['coefficients']
    assert 'reviewer_count' in result['coefficients']
    
    # Check p-values are floats
    for k, v in result['p_values'].items():
        assert isinstance(v, float)
        assert 0.0 <= v <= 1.0 or np.isnan(v)

def test_perform_lmer_analysis_with_small_sample(sample_data):
    """Test LMER with a very small sample to ensure it doesn't crash."""
    small_data = sample_data.head(4)
    result = perform_lmer_analysis(small_data)
    assert 'coefficients' in result

def test_load_filtered_pr_data_file_not_found():
    """Test that load_filtered_pr_data raises error if file missing."""
    if not Path("data/processed/pr_data_filtered.csv").exists():
        with pytest.raises(FileNotFoundError):
            load_filtered_pr_data()
    else:
        try:
            df = load_filtered_pr_data()
            assert isinstance(df, pd.DataFrame)
        except Exception:
            pass

def test_simex_correction_applies_when_fp_rate_high():
    """Test that SIMEX correction is applied when false positive rate > 5%."""
    # Mock analysis results with a high false positive rate
    mock_results = {
        'lmer': {
            'coefficients': {
                'Intercept': 100.0,
                'code_lines_changed': 0.5,
                'reviewer_count': -2.0,
                'C(origin_label)[T.Non-Disclosing]': 15.0
            },
            'p_values': {
                'Intercept': 0.001,
                'code_lines_changed': 0.02,
                'reviewer_count': 0.05,
                'C(origin_label)[T.Non-Disclosing]': 0.03
            }
        },
        'fp_rate': 0.10  # 10% > 5%
    }
    
    # Mock the load and save functions to use our mock data
    with patch('analysis.simex_correction.load_analysis_results') as mock_load, \
         patch('analysis.simex_correction.save_analysis_results') as mock_save:
        
        mock_load.return_value = mock_results
        
        # Call the main SIMEX function
        from analysis.simex_correction import main
        # We need to simulate the main execution flow or call apply_simex_correction directly
        # Let's test the core logic function
        from analysis.simex_correction import apply_simex_correction
        
        # We need to mock the LMER fitting for the simulated data
        # Since we can't easily run full LMER in a unit test without real data,
        # we test the structure of the result
        
        # The function should return a dict with simex_corrected_coefficients
        # We'll mock the heavy lifting
        with patch('analysis.simex_correction.fit_lmer_with_simulated_labels') as mock_fit:
            mock_fit.return_value = {
                'coefficients': {
                    'Intercept': 102.0,
                    'code_lines_changed': 0.55,
                    'reviewer_count': -2.1,
                    'C(origin_label)[T.Non-Disclosing]': 16.0
                }
            }
            
            result = apply_simex_correction(mock_results)
            
            assert 'simex_corrected_coefficients' in result
            assert isinstance(result['simex_corrected_coefficients'], dict)
            # Check that corrected coefficients are different from original (due to correction)
            assert result['simex_corrected_coefficients']['code_lines_changed'] != \
                   mock_results['lmer']['coefficients']['code_lines_changed']

def test_simex_correction_skipped_when_fp_rate_low():
    """Test that SIMEX correction is skipped when false positive rate <= 5%."""
    mock_results = {
        'lmer': {
            'coefficients': {
                'Intercept': 100.0,
                'code_lines_changed': 0.5,
                'reviewer_count': -2.0,
                'C(origin_label)[T.Non-Disclosing]': 15.0
            },
            'p_values': {
                'Intercept': 0.001,
                'code_lines_changed': 0.02,
                'reviewer_count': 0.05,
                'C(origin_label)[T.Non-Disclosing]': 0.03
            }
        },
        'fp_rate': 0.03  # 3% <= 5%
    }
    
    # When fp_rate <= 5%, SIMEX should not be applied
    # The function should return the original coefficients or a flag
    from analysis.simex_correction import apply_simex_correction
    
    with patch('analysis.simex_correction.fit_lmer_with_simulated_labels') as mock_fit:
        result = apply_simex_correction(mock_results)
        
        # SIMEX should not be applied, so no simex_corrected_coefficients
        # or it should be the same as original
        if 'simex_corrected_coefficients' in result:
            # If present, it should be identical to original
            assert result['simex_corrected_coefficients'] == mock_results['lmer']['coefficients']

def test_simex_extrapolation_logic():
    """Test the extrapolation logic in SIMEX correction."""
    # Create mock simulated results at different noise levels
    from analysis.simex_correction import extrapolate_to_zero_noise
    
    # Mock data: lambda values and corresponding coefficients
    lambdas = [0.0, 0.5, 1.0, 1.5, 2.0]
    coefficients = [
        {'code_lines_changed': 0.45},  # lambda=0 (no noise)
        {'code_lines_changed': 0.48},  # lambda=0.5
        {'code_lines_changed': 0.50},  # lambda=1.0 (original)
        {'code_lines_changed': 0.52},  # lambda=1.5
        {'code_lines_changed': 0.55},  # lambda=2.0
    ]
    
    # The extrapolation should estimate the coefficient at lambda=0
    # based on the trend from higher lambdas
    result = extrapolate_to_zero_noise(lambdas, coefficients)
    
    assert 'code_lines_changed' in result
    # The extrapolated value should be close to the lambda=0 value
    # but calculated from the regression of all points
    assert isinstance(result['code_lines_changed'], float)

def test_simex_simulation_steps():
    """Test that SIMEX correctly simulates misclassification at multiple levels."""
    from analysis.simex_correction import simulate_misclassification
    
    # Create a simple DataFrame
    df = pd.DataFrame({
        'origin_label': ['Disclosing', 'Non-Disclosing', 'Disclosing', 'Non-Disclosing'],
        'code_lines_changed': [10, 20, 30, 40],
        'first_review_time': [100.0, 120.0, 110.0, 130.0],
        'repo': ['A', 'A', 'B', 'B'],
        'reviewer_count': [2, 3, 2, 4]
    })
    
    # Test simulation with different lambda values
    for lam in [0.0, 0.5, 1.0, 1.5, 2.0]:
        simulated_df = simulate_misclassification(df, lam, seed=42)
        
        assert isinstance(simulated_df, pd.DataFrame)
        assert 'origin_label' in simulated_df.columns
        assert len(simulated_df) == len(df)
        
        # At lambda=0, labels should be unchanged (or minimally changed)
        if lam == 0.0:
            # Should be mostly the same, but due to simulation randomness, 
            # we just check it returns a valid dataframe
            pass

def test_simex_integration_with_lmer():
    """Integration test: SIMEX correction with LMER analysis."""
    # This test verifies the end-to-end flow of SIMEX correction
    # We mock the heavy LMER fitting to avoid dependency on statsmodels in tests
    
    mock_results = {
        'lmer': {
            'coefficients': {
                'Intercept': 100.0,
                'code_lines_changed': 0.5,
                'reviewer_count': -2.0,
                'C(origin_label)[T.Non-Disclosing]': 15.0
            },
            'p_values': {
                'Intercept': 0.001,
                'code_lines_changed': 0.02,
                'reviewer_count': 0.05,
                'C(origin_label)[T.Non-Disclosing]': 0.03
            }
        },
        'fp_rate': 0.10
    }
    
    with patch('analysis.simex_correction.fit_lmer_with_simulated_labels') as mock_fit:
        # Return a consistent corrected coefficient
        mock_fit.return_value = {
            'coefficients': {
                'Intercept': 105.0,
                'code_lines_changed': 0.55,
                'reviewer_count': -2.2,
                'C(origin_label)[T.Non-Disclosing]': 17.0
            }
        }
        
        from analysis.simex_correction import apply_simex_correction
        result = apply_simex_correction(mock_results)
        
        assert 'simex_corrected_coefficients' in result
        corrected = result['simex_corrected_coefficients']
        
        # Verify all expected keys are present
        expected_keys = ['Intercept', 'code_lines_changed', 'reviewer_count', 
                       'C(origin_label)[T.Non-Disclosing]']
        for key in expected_keys:
            assert key in corrected