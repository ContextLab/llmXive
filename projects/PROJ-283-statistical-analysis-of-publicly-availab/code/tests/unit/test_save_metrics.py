"""
Unit tests for T027: save_model_metrics functionality.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from src.models.fit import save_model_metrics, validate_against_schema, load_schema

class TestSaveMetrics:
    def test_save_model_metrics_creates_file(self, tmp_path):
        """Test that save_model_metrics creates the output file."""
        # Mock paths
        results_dir = tmp_path / "data" / "results"
        results_dir.mkdir(parents=True)
        
        # Create a mock schema file
        schema_path = tmp_path / "specs" / "contracts"
        schema_path.mkdir(parents=True)
        schema_file = schema_path / "model_output.schema.yaml"
        schema_content = """
        description: "Test Schema"
        columns:
          - name: model_type
            type: string
        """
        schema_file.write_text(schema_content)
        
        # Mock global paths
        with patch('src.models.fit.RESULTS_DIR', results_dir), \
             patch('src.models.fit.SCHEMA_PATH', schema_file):
            
            beta_result = {
                'model_type': 'Beta Regression',
                'coefficients': [0.5, 0.2],
                'p_values': [0.005, 0.1],
                'r_squared': 0.8,
                'aic': 100.0,
                'feature_names': ['feat1', 'feat2']
            }
            
            ridge_result = {
                'model_type': 'Ridge Regression',
                'coefficients': [0.3, 0.1],
                'p_values': [],
                'r_squared': 0.75,
                'aic': np.nan,
                'cross_validation_scores': [0.7, 0.8],
                'feature_names': ['feat1', 'feat2']
            }
            
            # Create dummy corrected p-values
            corrected_pvals = pd.DataFrame({
                'original_p_value': [0.005, 0.1],
                'corrected_p_value': [0.01, 0.2]
            })
            
            save_model_metrics(beta_result, ridge_result, corrected_pvals)
            
            output_path = results_dir / "model_metrics.json"
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert 'models' in data
            assert len(data['models']) == 2
            assert data['models'][0]['model_type'] == 'Beta Regression'
            assert 'significant_predictors' in data['models'][0]
    
    def test_validate_against_schema_valid(self):
        """Test validation with valid data."""
        schema = {
            "description": "Test",
            "columns": [{"name": "model_type", "type": "string"}]
        }
        data = {
            "models": [
                {
                    "model_type": "Beta",
                    "coefficients": [1.0],
                    "p_values": [0.05],
                    "r_squared": 0.9,
                    "aic": 10.0
                }
            ]
        }
        assert validate_against_schema(data, schema) is True
    
    def test_validate_against_schema_invalid(self):
        """Test validation with missing required keys."""
        schema = {
            "description": "Test",
            "columns": [{"name": "model_type", "type": "string"}]
        }
        data = {
            "wrong_key": "value"
        }
        assert validate_against_schema(data, schema) is False
    
    def test_load_schema_file_not_found(self):
        """Test loading a non-existent schema."""
        with pytest.raises(FileNotFoundError):
            load_schema(Path("/nonexistent/path.yaml"))
    
    def test_save_model_metrics_empty_pvalues(self):
        """Test saving when p-values are empty."""
        tmp_path = Path(tempfile.mkdtemp())
        results_dir = tmp_path / "data" / "results"
        results_dir.mkdir(parents=True)
        
        schema_path = tmp_path / "specs" / "contracts"
        schema_path.mkdir(parents=True)
        schema_file = schema_path / "model_output.schema.yaml"
        schema_file.write_text("description: test")
        
        beta_result = {
            'model_type': 'Beta Regression',
            'coefficients': [0.5],
            'p_values': [],
            'r_squared': 0.8,
            'aic': 100.0,
            'feature_names': ['feat1']
        }
        
        ridge_result = {
            'model_type': 'Ridge Regression',
            'coefficients': [0.3],
            'p_values': [],
            'r_squared': 0.75,
            'aic': np.nan,
            'cross_validation_scores': [0.7],
            'feature_names': ['feat1']
        }
        
        with patch('src.models.fit.RESULTS_DIR', results_dir), \
             patch('src.models.fit.SCHEMA_PATH', schema_file):
            save_model_metrics(beta_result, ridge_result, None)
            
            output_path = results_dir / "model_metrics.json"
            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert data['models'][0]['significant_predictors'] == []