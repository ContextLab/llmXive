"""
Contract Test for Dataset Schema Validation (Task T010).

Verifies that the dataset schema matches the expected structure
and that validation logic works correctly.
"""
import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingest import load_required_variables, validate_variables

class TestDatasetSchema:
    """Test cases for dataset schema validation."""

    def test_required_variables_loaded(self):
        """Test that required variables are loaded from config."""
        required = load_required_variables()
        
        assert 'required_predictors' in required
        assert 'required_outcomes' in required
        assert isinstance(required['required_predictors'], list)
        assert isinstance(required['required_outcomes'], list)

    def test_validation_passes_with_complete_data(self):
        """Test validation passes when all required variables are present."""
        # Create a complete dataset
        df = pd.DataFrame({
            'subject_id': range(10),
            'taxon_abundance': np.random.rand(10),
            'relative_abundance': np.random.rand(10),
            'rem_duration': np.random.rand(10) * 100,
            'sws_duration': np.random.rand(10) * 100,
            'total_sleep_time': np.random.rand(10) * 100
        })
        
        required = {
            'required_predictors': ['taxon_abundance', 'relative_abundance'],
            'required_outcomes': ['rem_duration', 'sws_duration', 'total_sleep_time']
        }
        
        is_valid, metrics = validate_variables(df, required)
        
        assert is_valid is True
        assert metrics['missing_predictors'] == []
        assert metrics['missing_outcomes'] == []

    def test_validation_fails_with_missing_predictor(self):
        """Test validation fails when a predictor is missing."""
        df = pd.DataFrame({
            'subject_id': range(10),
            'relative_abundance': np.random.rand(10),
            'rem_duration': np.random.rand(10) * 100,
            'sws_duration': np.random.rand(10) * 100,
            'total_sleep_time': np.random.rand(10) * 100
        })
        
        required = {
            'required_predictors': ['taxon_abundance', 'relative_abundance'],
            'required_outcomes': ['rem_duration', 'sws_duration', 'total_sleep_time']
        }
        
        with pytest.raises(ValueError, match="Missing required variables"):
            validate_variables(df, required)

    def test_validation_fails_with_missing_outcome(self):
        """Test validation fails when an outcome is missing."""
        df = pd.DataFrame({
            'subject_id': range(10),
            'taxon_abundance': np.random.rand(10),
            'relative_abundance': np.random.rand(10),
            'rem_duration': np.random.rand(10) * 100,
            'sws_duration': np.random.rand(10) * 100
        })
        
        required = {
            'required_predictors': ['taxon_abundance', 'relative_abundance'],
            'required_outcomes': ['rem_duration', 'sws_duration', 'total_sleep_time']
        }
        
        with pytest.raises(ValueError, match="Missing required variables"):
            validate_variables(df, required)

    def test_metrics_report_accuracy(self):
        """Test that validation metrics accurately reflect missing variables."""
        df = pd.DataFrame({
            'subject_id': range(10),
            'taxon_abundance': np.random.rand(10),
            'rem_duration': np.random.rand(10) * 100
        })
        
        required = {
            'required_predictors': ['taxon_abundance', 'relative_abundance'],
            'required_outcomes': ['rem_duration', 'sws_duration', 'total_sleep_time']
        }
        
        with pytest.raises(ValueError):
            is_valid, metrics = validate_variables(df, required)
            assert metrics['missing_predictors'] == ['relative_abundance']
            assert metrics['missing_outcomes'] == ['sws_duration', 'total_sleep_time']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
