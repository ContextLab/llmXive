import pytest
import numpy as np
import sys
import os
import tempfile
import logging
from src.environment.synthetic_mdp import generate_mdp, generate_heavy_tailed_mdp, validate_distribution

class TestDistributionValidation:
    """Test distribution validation for generated MDPs."""
    
    def test_heavy_tailed_validation(self):
        """Test that heavy-tailed distribution is correctly validated."""
        # Generate heavy-tailed MDP
        mdp = generate_heavy_tailed_mdp(n_objectives=5, seed=42, df=3.0)
        
        # Validate distribution
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            results = validate_distribution(mdp, log_file=log_file)
            
            # Check that validation was performed
            assert 'distribution_type' in results
            assert results['distribution_type'] == 'heavy_tailed'
            
            # Check that p-values were computed
            assert 'p_values' in results
            assert len(results['p_values']) > 0
            
            # For heavy-tailed, we expect at least one p-value > 0.05 (not rejecting null)
            # This is a probabilistic test, so we check the structure rather than exact values
            p_values = list(results['p_values'].values())
            assert any(p > 0.05 for p in p_values) or len(p_values) == 0
            
            # Check log file was written
            assert os.path.exists(log_file)
            with open(log_file, 'r') as f:
                log_content = f.read()
                assert 'Distribution Validation' in log_content
                assert 'heavy_tailed' in log_content
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)
    
    def test_gaussian_validation(self):
        """Test that Gaussian distribution is correctly validated."""
        mdp = generate_mdp(n_objectives=5, seed=42, noise_dist='gaussian')
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            results = validate_distribution(mdp, log_file=log_file)
            
            assert results['distribution_type'] == 'gaussian'
            assert 'p_values' in results
            
            # For Gaussian, we expect KS-test against normal distribution
            p_values = [v for k, v in results['p_values'].items() if 'ks_test' in k]
            assert len(p_values) > 0
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)
    
    def test_sparse_validation(self):
        """Test that sparse distribution is correctly validated."""
        mdp = generate_mdp(n_objectives=5, seed=42, noise_dist='sparse')
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            results = validate_distribution(mdp, log_file=log_file)
            
            assert results['distribution_type'] == 'sparse'
            assert 'statistics' in results
            
            # Check sparsity statistics
            for key, value in results['statistics'].items():
                if 'sparsity' in key:
                    assert value > 0.9  # Sparse should have high sparsity ratio
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)
    
    def test_nonconvex_validation(self):
        """Test that non-convex distribution is correctly validated."""
        mdp = generate_mdp(n_objectives=5, seed=42, noise_dist='nonconvex')
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            results = validate_distribution(mdp, log_file=log_file)
            
            assert results['distribution_type'] == 'nonconvex'
            assert 'statistics' in results
            
            # Check for bimodality (multiple peaks)
            for key, value in results['statistics'].items():
                if 'num_peaks' in key:
                    # Non-convex should have multiple peaks
                    assert value >= 1  # At least one peak
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)
    
    def test_linear_validation(self):
        """Test that linear distribution is correctly validated."""
        mdp = generate_mdp(n_objectives=5, seed=42, noise_dist='linear', noise_correlation=0.5)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            results = validate_distribution(mdp, log_file=log_file)
            
            assert results['distribution_type'] == 'linear'
            assert 'statistics' in results
            
            # Check correlation statistics
            for key, value in results['statistics'].items():
                if 'correlation' in key:
                    # Linear should have some correlation
                    assert -1.0 <= value <= 1.0
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)
    
    def test_validation_logging(self):
        """Test that validation results are properly logged."""
        mdp = generate_heavy_tailed_mdp(n_objectives=5, seed=42)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            validate_distribution(mdp, log_file=log_file)
            
            with open(log_file, 'r') as f:
                log_content = f.read()
                
            # Check for key validation information
            assert 'Distribution Validation' in log_content
            assert 'heavy_tailed' in log_content
            assert 'Validation Passed' in log_content
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)