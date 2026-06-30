"""
Integration tests for the analysis pipeline components.
These tests verify that the components work together correctly.
"""
import pytest
import numpy as np
from typing import List
from analysis.dynamics import detect_communities, calculate_flexibility
from analysis.statistics import fit_regression, run_permutation_test
from analysis.connectivity import compute_static_connectivity_strength

class TestAnalysisPipelineIntegration:
    def test_full_analysis_flow(self):
        """Test a simplified full analysis flow from connectivity to regression."""
        np.random.seed(42)
        n_subjects = 50
        n_timepoints = 100
        n_rois = 5
        
        # Simulate fMRI data for each subject
        fmri_data = np.random.randn(n_subjects, n_timepoints, n_rois)
        
        # Step 1: Compute static connectivity strength
        static_strengths = []
        for i in range(n_subjects):
            strength = compute_static_connectivity_strength(fmri_data[i])
            static_strengths.append(strength)
        
        assert len(static_strengths) == n_subjects
        assert all(isinstance(s, float) for s in static_strengths)
        
        # Step 2: Simulate community detection and flexibility calculation
        # (In reality, this would use sliding window connectivity)
        # For this test, we'll create synthetic community label sequences
        community_labels_list: List[List[List[int]]] = []
        for i in range(n_subjects):
            # Generate 5 time windows of community labels
            window_labels = [
                np.random.randint(0, 3, n_rois).tolist()
                for _ in range(5)
            ]
            community_labels_list.append(window_labels)
        
        flexibilities = [calculate_flexibility(labels) for labels in community_labels_list]
        
        assert len(flexibilities) == n_subjects
        assert all(0.0 <= f <= 1.0 for f in flexibilities)
        
        # Step 3: Simulate creativity scores
        creativity_scores = np.array([
            0.5 * f + np.random.randn() * 0.3 
            for f in flexibilities
        ])
        
        # Step 4: Run regression
        covariates = {
            'age': np.random.randn(n_subjects),
            'sex': np.random.randint(0, 2, n_subjects),
            'education': np.random.randn(n_subjects),
            'static_connectivity_strength': np.array(static_strengths)
        }
        
        result = fit_regression(
            np.array(flexibilities), 
            creativity_scores, 
            covariates
        )
        
        assert result.r_squared is not None
        assert result.p_value is not None
        
        # Step 5: Run permutation test
        p_perm = run_permutation_test(
            np.array(flexibilities), 
            creativity_scores, 
            n_permutations=100
        )
        
        assert 0 <= p_perm <= 1

    def test_flexibility_range_validation(self):
        """Test that flexibility values are always in valid range [0, 1]."""
        np.random.seed(42)
        
        for _ in range(100):
            n_windows = np.random.randint(1, 10)
            n_rois = np.random.randint(2, 10)
            
            # Generate random community labels
            community_labels = [
                np.random.randint(0, 5, n_rois).tolist()
                for _ in range(n_windows)
            ]
            
            flexibility = calculate_flexibility(community_labels)
            
            assert 0.0 <= flexibility <= 1.0, \
                f"Flexibility {flexibility} out of range [0, 1]"

    def test_regression_coefficients_significance(self):
        """Test that regression coefficients have expected properties."""
        np.random.seed(42)
        n = 100
        
        # Create data with known relationship
        flexibility = np.random.randn(n)
        creativity = 0.6 * flexibility + np.random.randn(n) * 0.4
        covariates = {'age': np.random.randn(n)}
        
        result = fit_regression(flexibility, creativity, covariates)
        
        # The coefficient for flexibility should be positive
        assert result.coef_flexibility > 0, \
            "Expected positive coefficient for flexibility"
        
        # R-squared should be positive
        assert result.r_squared > 0, \
            "Expected positive R-squared"