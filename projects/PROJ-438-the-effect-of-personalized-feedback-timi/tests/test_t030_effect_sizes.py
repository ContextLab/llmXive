"""
Unit tests for T030: Extraction of Cohen's d effect sizes and p-values.

Tests the logic of extract_effect_sizes and the integration of fit_cluster_robust_ols
without requiring the full OULAD dataset.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent / 'code'
sys.path.insert(0, str(code_dir))

from models import extract_effect_sizes, fit_cluster_robust_ols

def create_dummy_data(n=100):
    """
    Creates a deterministic dummy dataset for testing.
    Groups: Immediate, Delayed, Variable
    """
    np.random.seed(42)
    
    # Create groups with known differences
    # Immediate: mean=80, std=10
    # Delayed: mean=70, std=10
    # Variable: mean=75, std=10
    
    n_per_group = n // 3
    remainder = n % 3
    
    data = []
    
    # Immediate
    for i in range(n_per_group + (1 if remainder > 0 else 0)):
        data.append({
            'student_id': f's_{i}',
            'course_id': 'course_A',
            'feedback_group': 'Immediate',
            'final_grade': np.random.normal(80, 10)
        })
    
    # Delayed
    start_idx = n_per_group + (1 if remainder > 0 else 0)
    for i in range(n_per_group + (1 if remainder > 1 else 0)):
        data.append({
            'student_id': f's_{start_idx + i}',
            'course_id': 'course_B',
            'feedback_group': 'Delayed',
            'final_grade': np.random.normal(70, 10)
        })
        
    # Variable
    start_idx = n_per_group + (1 if remainder > 0 else 0) + n_per_group + (1 if remainder > 1 else 0)
    count = n_per_group + (1 if remainder == 2 else 0)
    for i in range(count):
        data.append({
            'student_id': f's_{start_idx + i}',
            'course_id': 'course_C',
            'feedback_group': 'Variable',
            'final_grade': np.random.normal(75, 10)
        })
        
    return pd.DataFrame(data)

class TestExtractEffectSizes:
    
    def test_effect_sizes_computation(self):
        """Test that effect sizes are computed correctly for known groups."""
        data = create_dummy_data(300)
        
        # We mock the model results object since we are testing the extraction logic
        # which relies on data statistics and scipy t-tests
        # The function signature requires model_results, but we can pass None 
        # if we refactor, but currently it uses it for summary. 
        # Looking at the code, model_results is passed but not strictly used 
        # inside extract_effect_sizes for the calculation (only for info if we added it).
        # The calculation uses scipy ttest_ind.
        
        # To satisfy the signature, we create a dummy object
        class DummyResults:
            pass
        
        results = extract_effect_sizes(data, DummyResults())
        
        assert isinstance(results, pd.DataFrame)
        assert 'cohens_d' in results.columns
        assert 'p_value' in results.columns
        assert 'group1' in results.columns
        assert 'group2' in results.columns
        
        # Check we have 3 comparisons (Immediate-Delayed, Immediate-Variable, Delayed-Variable)
        assert len(results) == 3
        
    def test_cohens_d_sign(self):
        """Test that Cohen's d has the correct sign (Immediate > Delayed)."""
        data = create_dummy_data(300)
        
        class DummyResults:
            pass
        
        results = extract_effect_sizes(data, DummyResults())
        
        # Find Immediate vs Delayed comparison
        # Note: order depends on iteration, so we check both directions
        im_vs_de = results[
            ((results['group1'] == 'Immediate') & (results['group2'] == 'Delayed')) |
            ((results['group1'] == 'Delayed') & (results['group2'] == 'Immediate'))
        ]
        
        assert len(im_vs_de) == 1
        
        # Immediate mean (80) > Delayed mean (70), so difference should be positive if group1=Immediate
        # If group1=Delayed, difference is negative.
        row = im_vs_de.iloc[0]
        
        if row['group1'] == 'Immediate':
            assert row['cohens_d'] > 0
        else:
            assert row['cohens_d'] < 0
            
    def test_p_values_validity(self):
        """Test that p-values are between 0 and 1."""
        data = create_dummy_data(300)
        
        class DummyResults:
            pass
        
        results = extract_effect_sizes(data, DummyResults())
        
        assert all(results['p_value'] >= 0)
        assert all(results['p_value'] <= 1)
        
    def test_no_data_error(self):
        """Test that empty data raises an error."""
        data = pd.DataFrame(columns=['final_grade', 'feedback_group', 'course_id'])
        
        class DummyResults:
            pass
        
        with pytest.raises(ValueError):
            extract_effect_sizes(data, DummyResults())

class TestFitClusterRobustOLS:
    
    def test_model_fitting(self):
        """Test that the model fits without error."""
        data = create_dummy_data(300)
        
        # This should not raise
        results = fit_cluster_robust_ols(data)
        
        assert results is not None
        assert hasattr(results, 'params')
        assert hasattr(results, 'bse')

if __name__ == '__main__':
    pytest.main([__file__, '-v'])