"""
Unit tests for VIF compliance verification (Task T030).

Tests the verify_vif_compliance.py module to ensure it correctly
verifies that independent effect claims are suppressed when VIF > 5.
"""
import os
import sys
import pytest
from pathlib import Path
import pandas as pd
import yaml
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent.parent / 'code'
sys.path.insert(0, str(code_dir))

from verify_vif_compliance import (
    load_model_results,
    load_vif_status,
    verify_vif_suppression_logic,
    generate_final_verification_report
)

class TestLoadModelResults:
    """Tests for load_model_results function."""
    
    def test_load_valid_model_results(self, tmp_path):
        """Test loading a valid model results file."""
        # Create a valid CSV file
        csv_path = tmp_path / 'model_results.csv'
        data = {
            'model_type': ['ols', 'rf', 'pgl'],
            'predictor': ['depth', 'surface_area', 'depth'],
            'coefficient': [0.5, 0.3, 0.4],
            'p_value': [0.01, 0.02, 0.015],
            'r2': [0.6, 0.55, 0.62],
            'adj_p_value': [0.02, 0.03, 0.025]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        
        # Load and verify
        loaded_df = load_model_results(csv_path)
        
        assert len(loaded_df) == 3
        assert set(loaded_df.columns) == {
            'model_type', 'predictor', 'coefficient', 
            'p_value', 'r2', 'adj_p_value'
        }
        assert loaded_df.iloc[0]['predictor'] == 'depth'
    
    def test_load_missing_file_raises_error(self, tmp_path):
        """Test that loading a missing file raises FileNotFoundError."""
        missing_path = tmp_path / 'nonexistent.csv'
        
        with pytest.raises(FileNotFoundError):
            load_model_results(missing_path)
    
    def test_load_empty_file_raises_error(self, tmp_path):
        """Test that loading an empty file raises ValueError."""
        csv_path = tmp_path / 'empty.csv'
        csv_path.touch()
        
        with pytest.raises(ValueError):
            load_model_results(csv_path)
    
    def test_load_missing_columns_raises_error(self, tmp_path):
        """Test that loading a file with missing columns raises ValueError."""
        csv_path = tmp_path / 'incomplete.csv'
        data = {
            'model_type': ['ols'],
            'predictor': ['depth']
            # Missing other required columns
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        
        with pytest.raises(ValueError):
            load_model_results(csv_path)

class TestLoadVifStatus:
    """Tests for load_vif_status function."""
    
    def test_load_valid_vif_status(self, tmp_path):
        """Test loading a valid VIF status file."""
        yaml_path = tmp_path / 'vif_status.yaml'
        data = {
            'vif_exceeded': True,
            'suppressed_claims': ['depth', 'surface_area'],
            'framing_applied': True,
            'max_vif': 8.5
        }
        
        with open(yaml_path, 'w') as f:
            yaml.dump(data, f)
        
        loaded_data = load_vif_status(yaml_path)
        
        assert loaded_data['vif_exceeded'] is True
        assert len(loaded_data['suppressed_claims']) == 2
        assert loaded_data['framing_applied'] is True
    
    def test_load_missing_file_raises_error(self, tmp_path):
        """Test that loading a missing file raises FileNotFoundError."""
        missing_path = tmp_path / 'nonexistent.yaml'
        
        with pytest.raises(FileNotFoundError):
            load_vif_status(missing_path)
    
    def test_load_empty_file_raises_error(self, tmp_path):
        """Test that loading an empty file raises ValueError."""
        yaml_path = tmp_path / 'empty.yaml'
        yaml_path.touch()
        
        with pytest.raises(ValueError):
            load_vif_status(yaml_path)

class TestVerifyVifSuppressionLogic:
    """Tests for verify_vif_suppression_logic function."""
    
    def test_vif_not_exceeded_passes(self):
        """Test that verification passes when VIF is not exceeded."""
        model_results = pd.DataFrame({
            'model_type': ['ols'],
            'predictor': ['depth'],
            'coefficient': [0.5],
            'p_value': [0.01],
            'r2': [0.6],
            'adj_p_value': [0.02]
        })
        
        vif_status = {
            'vif_exceeded': False,
            'max_vif': 3.2
        }
        
        result = verify_vif_suppression_logic(model_results, vif_status)
        
        assert result['compliance_status'] == 'PASS'
        assert len(result['errors']) == 0
        assert 'VIF threshold (5) was not exceeded' in result['details'][0]
    
    def test_vif_exceeded_without_suppression_fails(self):
        """Test that verification fails when VIF exceeded but no suppression recorded."""
        model_results = pd.DataFrame({
            'model_type': ['ols'],
            'predictor': ['depth'],
            'coefficient': [0.5],
            'p_value': [0.01],
            'r2': [0.6],
            'adj_p_value': [0.02]
        })
        
        vif_status = {
            'vif_exceeded': True,
            'max_vif': 8.5
            # Missing 'suppressed_claims'
        }
        
        result = verify_vif_suppression_logic(model_results, vif_status)
        
        assert result['compliance_status'] == 'FAIL'
        assert len(result['errors']) > 0
        assert any('no suppressed claims recorded' in err for err in result['errors'])
    
    def test_vif_exceeded_with_suppression_passes(self):
        """Test that verification passes when VIF exceeded and suppression recorded."""
        model_results = pd.DataFrame({
            'model_type': ['ols', 'rf'],
            'predictor': ['depth', 'surface_area'],
            'coefficient': [0.5, 0.3],
            'p_value': [0.01, 0.02],
            'r2': [0.6, 0.55],
            'adj_p_value': [0.02, 0.03]
        })
        
        vif_status = {
            'vif_exceeded': True,
            'suppressed_claims': ['depth', 'surface_area'],
            'framing_applied': True,
            'max_vif': 8.5
        }
        
        result = verify_vif_suppression_logic(model_results, vif_status)
        
        assert result['compliance_status'] in ['PASS', 'WARNING']
        assert len(result['errors']) == 0
        assert 'Suppressed 2 variables' in result['details'][0]
    
    def test_vif_exceeded_with_significant_results_warns(self):
        """Test that verification warns when suppressed variables have significant results."""
        model_results = pd.DataFrame({
            'model_type': ['ols'],
            'predictor': ['depth'],
            'coefficient': [0.5],
            'p_value': [0.001],
            'r2': [0.6],
            'adj_p_value': [0.002]  # Significant
        })
        
        vif_status = {
            'vif_exceeded': True,
            'suppressed_claims': ['depth'],
            'framing_applied': True,
            'max_vif': 8.5
        }
        
        result = verify_vif_suppression_logic(model_results, vif_status)
        
        # Should pass but with warnings
        assert result['compliance_status'] == 'WARNING'
        assert len(result['warnings']) > 0
        assert any('significant results' in w for w in result['warnings'])

class TestGenerateFinalVerificationReport:
    """Tests for generate_final_verification_report function."""
    
    def test_generates_valid_yaml(self, tmp_path):
        """Test that the function generates a valid YAML file."""
        output_path = tmp_path / 'vif_compliance_check.yaml'
        
        verification_result = {
            'verification_timestamp': '2024-01-01 12:00:00',
            'vif_exceeded': True,
            'compliance_status': 'PASS',
            'details': ['VIF exceeded. Suppressed 2 variables'],
            'warnings': [],
            'errors': []
        }
        
        generate_final_verification_report(verification_result, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            loaded_data = yaml.safe_load(f)
        
        assert loaded_data['compliance_status'] == 'PASS'
        assert 'summary' in loaded_data
        assert loaded_data['summary']['task_id'] == 'T030'
    
    def test_creates_parent_directories(self, tmp_path):
        """Test that the function creates parent directories if needed."""
        nested_path = tmp_path / 'subdir' / 'nested' / 'vif_compliance_check.yaml'
        
        verification_result = {
            'verification_timestamp': '2024-01-01 12:00:00',
            'vif_exceeded': False,
            'compliance_status': 'PASS',
            'details': [],
            'warnings': [],
            'errors': []
        }
        
        generate_final_verification_report(verification_result, nested_path)
        
        assert nested_path.exists()