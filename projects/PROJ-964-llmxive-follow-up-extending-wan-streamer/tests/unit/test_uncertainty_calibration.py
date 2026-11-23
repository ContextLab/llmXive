"""
Unit tests for uncertainty_calibration.py (Task T024).
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np
import torch

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from metrics.uncertainty_calibration import (
    calculate_correlation,
    CORRELATION_THRESHOLD,
    finalize_checkpoint
)
from models.gru_estimator import GRUEstimator


class TestUncertaintyCalibration:
    """Test suite for uncertainty calibration logic."""

    def test_calculate_correlation_positive(self):
        """Test that correlation is calculated correctly for positive correlation."""
        # Create data where uncertainty correlates with error
        y_true = torch.tensor([1.0, 2.0, 3.0, 4.0, 5.0])
        predictions = torch.tensor([1.1, 2.2, 2.8, 4.1, 5.2]) # Small errors
        uncertainties = torch.tensor([0.1, 0.2, 0.3, 0.4, 0.5]) # Low uncertainty for low error? 
        # Actually, we want uncertainty to correlate with ERROR magnitude.
        # Let's make errors: [0.1, 0.2, 0.2, 0.1, 0.2] -> uncertainties should match pattern
        
        y_true = torch.tensor([10.0, 20.0, 30.0, 40.0, 50.0])
        predictions = torch.tensor([10.0, 20.0, 30.0, 40.0, 50.0]) # Perfect? No, need error
        # Let's construct specific error pattern
        errors = torch.tensor([0.1, 0.5, 1.0, 1.5, 2.0])
        uncertainties = torch.tensor([0.1, 0.5, 1.0, 1.5, 2.0]) # Perfect correlation
        
        # y_true - predictions = errors
        y_true = torch.tensor([0.0, 0.0, 0.0, 0.0, 0.0])
        predictions = -errors
        
        corr = calculate_correlation(y_true, predictions, uncertainties)
        assert abs(corr - 1.0) < 0.01, f"Expected correlation ~1.0, got {corr}"

    def test_calculate_correlation_negative(self):
        """Test that correlation is calculated correctly for negative correlation."""
        errors = torch.tensor([2.0, 1.5, 1.0, 0.5, 0.1])
        uncertainties = torch.tensor([0.1, 0.5, 1.0, 1.5, 2.0]) # Inverse pattern
        
        y_true = torch.tensor([0.0, 0.0, 0.0, 0.0, 0.0])
        predictions = -errors
        
        corr = calculate_correlation(y_true, predictions, uncertainties)
        assert corr < 0.0, f"Expected negative correlation, got {corr}"

    def test_finalize_checkpoint_success(self, tmp_path):
        """Test successful checkpoint finalization."""
        pending_path = tmp_path / "estimator_checkpoint_pending.pt"
        final_path = tmp_path / "estimator_checkpoint_final.pt"
        state_path = tmp_path / "state.yaml"

        # Create dummy pending checkpoint
        dummy_model = GRUEstimator(input_dim=10, hidden_dim=16)
        torch.save({
            'model_state_dict': dummy_model.state_dict(),
            'model_config': {'input_dim': 10, 'hidden_dim': 16}
        }, pending_path)

        # Create dummy state
        with open(state_path, 'w') as f:
            f.write("project: test\n")

        # Mock the load/save functions to use our temp paths
        with patch('metrics.uncertainty_calibration.load_state_yaml') as mock_load, \
             patch('metrics.uncertainty_calibration.save_state_yaml') as mock_save, \
             patch('metrics.uncertainty_calibration.PENDING_CHECKPOINT_PATH', str(pending_path)), \
             patch('metrics.uncertainty_calibration.FINAL_CHECKPOINT_PATH', str(final_path)), \
             patch('metrics.uncertainty_calibration.STATE_YAML_PATH', str(state_path)):
            
            mock_load.return_value = {}
            
            # Should not raise
            finalize_checkpoint(0.8)

            # Verify final checkpoint exists
            assert final_path.exists(), "Final checkpoint was not created"
            
            # Verify save was called
            assert mock_save.called, "State was not updated"

    def test_finalize_checkpoint_failure(self, tmp_path):
        """Test that finalize_checkpoint raises error if correlation is low."""
        pending_path = tmp_path / "estimator_checkpoint_pending.pt"
        
        # Create dummy pending checkpoint
        dummy_model = GRUEstimator(input_dim=10, hidden_dim=16)
        torch.save({
            'model_state_dict': dummy_model.state_dict(),
            'model_config': {'input_dim': 10, 'hidden_dim': 16}
        }, pending_path)

        with patch('metrics.uncertainty_calibration.PENDING_CHECKPOINT_PATH', str(pending_path)):
            with pytest.raises(RuntimeError, match="Correlation .* is below threshold"):
                finalize_checkpoint(0.5) # Below 0.7 threshold

    def test_correlation_threshold_constant(self):
        """Verify the correlation threshold is set correctly."""
        assert CORRELATION_THRESHOLD == 0.7, "Threshold must be 0.7"