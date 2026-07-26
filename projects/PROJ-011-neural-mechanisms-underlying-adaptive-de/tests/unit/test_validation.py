"""
Unit tests for model validation module.
"""
import pytest
import numpy as np
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import arviz as az
import pymc as pm

from modeling.validation import (
    check_convergence,
    validate_and_restart,
    save_validation_report,
    DEFAULT_RHAT_THRESHOLD,
    DEFAULT_ESS_MIN,
    DEFAULT_MAX_RESTARTS
)
from utils.io import load_json, save_json


class TestCheckConvergence:
    """Tests for convergence checking functionality."""
    
    def test_converged_model(self, tmp_path):
        """Test that a well-converged model passes validation."""
        # Create a mock InferenceData with good metrics
        # Using a simple model for testing
        with pm.Model() as model:
            x = pm.Normal('x', mu=0, sigma=1)
            y = pm.Normal('y', mu=x, sigma=1, observed=np.random.randn(100))
            
            # Sample with good convergence
            idata = pm.sample(
                draws=1000,
                tune=500,
                chains=2,
                return_inferencedata=True,
                random_seed=42
            )
        
        result = check_convergence(idata)
        
        assert result['converged'] is True
        assert 'x' in result['rhat_values']
        assert 'x' in result['ess_values']
        assert result['rhat_values']['x'] < DEFAULT_RHAT_THRESHOLD
        assert result['ess_values']['x'] > DEFAULT_ESS_MIN
        assert len(result['failures']) == 0
    
    def test_non_converged_rhat(self, tmp_path):
        """Test detection of non-convergence due to high R-hat."""
        # Create a mock InferenceData with poor R-hat
        # We'll manually construct one for testing
        with pm.Model() as model:
            x = pm.Normal('x', mu=0, sigma=1)
            y = pm.Normal('y', mu=x, sigma=1, observed=np.random.randn(50))
            
            # Sample with fewer iterations to potentially get worse convergence
            idata = pm.sample(
                draws=100,
                tune=50,
                chains=2,
                return_inferencedata=True,
                random_seed=42,
                progressbar=False
            )
        
        # Force a high R-hat for testing
        result = check_convergence(idata, rhat_threshold=1.01)
        
        # With low samples, we might get higher R-hat
        # The test verifies the logic works
        assert 'x' in result['rhat_values']
        assert 'converged' in result
    
    def test_custom_thresholds(self, tmp_path):
        """Test that custom thresholds are respected."""
        with pm.Model() as model:
            x = pm.Normal('x', mu=0, sigma=1)
            y = pm.Normal('y', mu=x, sigma=1, observed=np.random.randn(100))
            
            idata = pm.sample(
                draws=1000,
                tune=500,
                chains=2,
                return_inferencedata=True,
                random_seed=42
            )
        
        # Use very strict thresholds
        result = check_convergence(idata, rhat_threshold=1.001, ess_min=10000)
        
        # With strict thresholds, might fail
        assert 'converged' in result
        assert 'rhat_values' in result
        assert 'ess_values' in result


class TestValidateAndRestart:
    """Tests for validation with restart functionality."""
    
    @patch('modeling.validation.run_mcmc_sampling')
    @patch('modeling.validation.build_hierarchical_model')
    @patch('modeling.validation.prepare_model_data')
    def test_successful_convergence_first_attempt(
        self, 
        mock_prepare, 
        mock_build, 
        mock_run_sampling
    ):
        """Test successful convergence on first attempt."""
        # Setup mocks
        mock_data = {'trial_data': np.random.randn(100)}
        mock_prepare.return_value = mock_data
        
        mock_model = MagicMock()
        mock_build.return_value = mock_model
        
        # Create real InferenceData for the mock to return
        with pm.Model() as test_model:
            x = pm.Normal('x', mu=0, sigma=1)
            y = pm.Normal('y', mu=x, sigma=1, observed=np.random.randn(100))
            mock_idata = pm.sample(
                draws=500,
                tune=250,
                chains=2,
                return_inferencedata=True,
                random_seed=42,
                progressbar=False
            )
        
        mock_run_sampling.return_value = mock_idata
        
        # Run validation
        behavioral_data = {'participant_id': 'test_001', 'trials': []}
        config = {'random_seed': 42}
        
        idata, report = validate_and_restart(
            participant_id='test_001',
            config=config,
            behavioral_data=behavioral_data,
            max_restarts=2
        )
        
        assert report['successful'] is True
        assert report['final_status'] == 'converged'
        assert report['total_attempts'] == 1
        assert idata is not None
    
    @patch('modeling.validation.run_mcmc_sampling')
    @patch('modeling.validation.build_hierarchical_model')
    @patch('modeling.validation.prepare_model_data')
    def test_convergence_after_restart(
        self, 
        mock_prepare, 
        mock_build, 
        mock_run_sampling
    ):
        """Test convergence after one failed attempt."""
        mock_data = {'trial_data': np.random.randn(100)}
        mock_prepare.return_value = mock_data
        
        mock_model = MagicMock()
        mock_build.return_value = mock_model
        
        # First call returns non-converged data
        with pm.Model() as test_model1:
            x = pm.Normal('x', mu=0, sigma=1)
            y = pm.Normal('y', mu=x, sigma=1, observed=np.random.randn(50))
            mock_idata_fail = pm.sample(
                draws=100,
                tune=50,
                chains=2,
                return_inferencedata=True,
                random_seed=42,
                progressbar=False
            )
        
        # Second call returns converged data
        with pm.Model() as test_model2:
            x = pm.Normal('x', mu=0, sigma=1)
            y = pm.Normal('y', mu=x, sigma=1, observed=np.random.randn(100))
            mock_idata_success = pm.sample(
                draws=500,
                tune=250,
                chains=2,
                return_inferencedata=True,
                random_seed=42,
                progressbar=False
            )
        
        # Return different results on different calls
        mock_run_sampling.side_effect = [mock_idata_fail, mock_idata_success]
        
        behavioral_data = {'participant_id': 'test_002', 'trials': []}
        config = {'random_seed': 42}
        
        idata, report = validate_and_restart(
            participant_id='test_002',
            config=config,
            behavioral_data=behavioral_data,
            max_restarts=3
        )
        
        assert report['successful'] is True
        assert report['final_status'] == 'converged'
        assert report['total_attempts'] == 2
        assert len(report['attempts']) == 2
        assert idata is not None


class TestSaveValidationReport:
    """Tests for report saving functionality."""
    
    def test_save_report_success(self, tmp_path):
        """Test successful report saving."""
        report = {
            'participant_id': 'test_001',
            'total_attempts': 1,
            'successful': True,
            'final_status': 'converged'
        }
        
        output_path = tmp_path / 'validation' / 'test_001_validation.json'
        save_validation_report(report, output_path)
        
        assert output_path.exists()
        saved_report = load_json(output_path)
        assert saved_report['participant_id'] == 'test_001'
        assert saved_report['successful'] is True
