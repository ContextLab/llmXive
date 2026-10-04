"""
Unit tests for Cox Proportional Hazards analysis (T035).

Tests the data preparation, model fitting, and result extraction logic.
Uses synthetic data generation for testing purposes, but the implementation
itself is designed to work with real data from T033.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from cox_ph_analysis import (
    load_convergence_data,
    prepare_cox_dataframe,
    run_cox_ph,
    save_results
)
from utils import MAX_EPOCHS

class TestLoadConvergenceData:
    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised when data file is missing."""
        # Create a temporary directory and set DATA_FILE to a non-existent path
        with patch('cox_ph_analysis.DATA_FILE', str(tmp_path / 'nonexistent.csv')):
            with pytest.raises(FileNotFoundError, match="Convergence data file not found"):
                load_convergence_data()
    
    def test_missing_columns(self, tmp_path):
        """Test that ValueError is raised when required columns are missing."""
        # Create a CSV with missing columns
        csv_path = tmp_path / 'convergence_logs.csv'
        df_missing = pd.DataFrame({
            'steps_to_convergence': [10, 20],
            'loss_type': ['ce', 'infonce']
            # Missing 'beta' and 'convergence_status'
        })
        df_missing.to_csv(csv_path, index=False)
        
        with patch('cox_ph_analysis.DATA_FILE', str(csv_path)):
            with pytest.raises(ValueError, match="Missing required columns"):
                load_convergence_data()
    
    def test_load_success(self, tmp_path):
        """Test successful loading of valid data."""
        csv_path = tmp_path / 'convergence_logs.csv'
        df_valid = pd.DataFrame({
            'steps_to_convergence': [10, 20, 30],
            'loss_type': ['ce', 'infonce', 'ce'],
            'beta': [0.0, 0.5, 1.0],
            'convergence_status': ['converged', 'censored', 'converged']
        })
        df_valid.to_csv(csv_path, index=False)
        
        with patch('cox_ph_analysis.DATA_FILE', str(csv_path)):
            result = load_convergence_data()
            
        assert len(result) == 3
        assert set(result.columns) == {'steps_to_convergence', 'loss_type', 'beta', 'convergence_status'}

class TestPrepareCoxDataFrame:
    def test_status_mapping(self):
        """Test that convergence_status is correctly mapped to event."""
        df = pd.DataFrame({
            'steps_to_convergence': [10, 20, 30],
            'loss_type': ['ce', 'infonce', 'ce'],
            'beta': [0.0, 0.5, 1.0],
            'convergence_status': ['converged', 'censored', 'converged']
        })
        
        result = prepare_cox_dataframe(df)
        
        assert 'event' in result.columns
        assert 'convergence_status' not in result.columns
        assert result['event'].tolist() == [1, 0, 1]
    
    def test_categorical_encoding(self):
        """Test that loss_type is converted to category."""
        df = pd.DataFrame({
            'steps_to_convergence': [10],
            'loss_type': ['ce'],
            'beta': [0.0],
            'convergence_status': ['converged']
        })
        
        result = prepare_cox_dataframe(df)
        
        assert result['loss_type'].dtype.name == 'category'
    
    def test_invalid_status_values(self):
        """Test that ValueError is raised for unknown status values."""
        df = pd.DataFrame({
            'steps_to_convergence': [10],
            'loss_type': ['ce'],
            'beta': [0.0],
            'convergence_status': ['unknown_status']
        })
        
        with pytest.raises(ValueError, match="Unknown convergence_status values"):
            prepare_cox_dataframe(df)

class TestRunCoxPh:
    def test_model_fitting(self):
        """Test that the Cox model fits successfully on valid data."""
        df = pd.DataFrame({
            'steps_to_convergence': [10, 20, 30, 40, 50, 60],
            'event': [1, 0, 1, 1, 0, 1],
            'loss_type': pd.Categorical(['ce', 'ce', 'infonce', 'ce', 'infonce', 'infonce']),
            'beta': [0.0, 0.0, 0.5, 0.5, 1.0, 1.0]
        })
        
        model, results = run_cox_ph(df)
        
        assert model is not None
        assert 'concordance_index' in results
        assert 'interaction_p_value' in results
        assert 'interaction_term' in results
    
    def test_interaction_term_extraction(self):
        """Test that the interaction term p-value is correctly extracted."""
        df = pd.DataFrame({
            'steps_to_convergence': [10, 20, 30, 40, 50, 60, 70, 80],
            'event': [1, 0, 1, 1, 0, 1, 1, 0],
            'loss_type': pd.Categorical(['ce', 'ce', 'ce', 'infonce', 'infonce', 'infonce', 'ce', 'infonce']),
            'beta': [0.0, 0.0, 0.5, 0.0, 0.5, 1.0, 1.0, 1.0]
        })
        
        _, results = run_cox_ph(df)
        
        # Check that interaction term exists and has a p-value
        assert results['interaction_term'] is not None
        assert isinstance(results['interaction_p_value'], float)
        assert 0 <= results['interaction_p_value'] <= 1

class TestSaveResults:
    def test_save_to_json(self, tmp_path):
        """Test that results are saved correctly to JSON."""
        # Create mock results
        results = {
            'concordance_index': 0.65,
            'interaction_p_value': 0.03,
            'interaction_term': 'loss_type_infonce:beta'
        }
        
        # Create a mock model
        mock_model = MagicMock()
        
        output_path = tmp_path / 'cox_results.json'
        model_path = tmp_path / 'cox_model_fitted.pkl'
        
        with patch('cox_ph_analysis.OUTPUT_FILE', str(output_path)):
            with patch('cox_ph_analysis.COX_MODEL_FILE', str(model_path)):
                save_results(results, mock_model)
        
        assert output_path.exists()
        assert model_path.exists()
        
        import json
        with open(output_path, 'r') as f:
            saved_results = json.load(f)
        
        assert saved_results['interaction_p_value'] == 0.03