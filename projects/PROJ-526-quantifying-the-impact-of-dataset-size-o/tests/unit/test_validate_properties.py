"""
Unit tests for property validation logic.

These tests verify that the validation logic correctly:
1. Counts distinct properties from a dataset
2. Raises ValueError when count < 15
3. Passes validation when count >= 15
4. Updates status file correctly
"""

import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate_properties import (
    count_distinct_properties,
    validate_property_count,
    update_properties_status,
    MIN_PROPERTIES_REQUIRED
)


class TestCountDistinctProperties:
    """Tests for the count_distinct_properties function."""
    
    def test_count_properties_with_parquet(self, tmp_path):
        """Test counting properties from a Parquet file."""
        # Create test data with 10 properties + metadata
        data = {
            'material_id': ['mat1', 'mat2'],
            'composition': ['Fe2O3', 'SiO2'],
            'prop1': [1.0, 2.0],
            'prop2': [3.0, 4.0],
            'prop3': [5.0, 6.0],
            'prop4': [7.0, 8.0],
            'prop5': [9.0, 10.0],
        }
        df = pd.DataFrame(data)
        
        parquet_path = tmp_path / "test.parquet"
        df.to_parquet(parquet_path)
        
        count = count_distinct_properties(parquet_path)
        
        # Should count prop1-5 (5 properties), excluding material_id and composition
        assert count == 5
    
    def test_count_properties_with_csv(self, tmp_path):
        """Test counting properties from a CSV file."""
        data = {
            'material_id': ['mat1', 'mat2'],
            'formula': ['Fe2O3', 'SiO2'],
            'band_gap': [2.0, 3.0],
            'formation_energy': [-1.0, -2.0],
            'elastic_modulus': [100.0, 200.0],
        }
        df = pd.DataFrame(data)
        
        csv_path = tmp_path / "test.csv"
        df.to_csv(csv_path, index=False)
        
        count = count_distinct_properties(csv_path)
        
        # Should count band_gap, formation_energy, elastic_modulus (3 properties)
        assert count == 3
    
    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            count_distinct_properties(tmp_path / "nonexistent.parquet")
    
    def test_unsupported_format(self, tmp_path):
        """Test that ValueError is raised for unsupported file format."""
        txt_path = tmp_path / "test.txt"
        txt_path.write_text("dummy content")
        
        with pytest.raises(ValueError):
            count_distinct_properties(txt_path)

class TestValidatePropertyCount:
    """Tests for the validate_property_count function."""
    
    @patch('validate_properties.load_processed_data_path')
    @patch('validate_properties.count_distinct_properties')
    @patch('validate_properties.update_properties_status')
    def test_validation_passes_with_sufficient_properties(self, mock_update, mock_count, mock_load, tmp_path):
        """Test that validation passes when count >= 15."""
        mock_load.return_value = tmp_path / "test.parquet"
        mock_count.return_value = 15
        
        # Create a mock config
        mock_config = MagicMock()
        mock_config.state_dir = str(tmp_path / "state")
        
        with patch('validate_properties.get_config', return_value=mock_config):
            result = validate_property_count()
        
        assert result is True
        mock_update.assert_called_once_with(15, True)
    
    @patch('validate_properties.load_processed_data_path')
    @patch('validate_properties.count_distinct_properties')
    @patch('validate_properties.update_properties_status')
    def test_validation_fails_with_insufficient_properties(self, mock_update, mock_count, mock_load, tmp_path):
        """Test that validation fails when count < 15."""
        mock_load.return_value = tmp_path / "test.parquet"
        mock_count.return_value = 10
        
        # Create a mock config
        mock_config = MagicMock()
        mock_config.state_dir = str(tmp_path / "state")
        
        with patch('validate_properties.get_config', return_value=mock_config):
            with pytest.raises(ValueError, match="CRITICAL: Property count"):
                validate_property_count()
        
        mock_update.assert_called_once_with(10, False)
    
    @patch('validate_properties.load_processed_data_path')
    def test_validation_raises_on_missing_file(self, mock_load, tmp_path):
        """Test that FileNotFoundError is raised when data file is missing."""
        mock_load.side_effect = FileNotFoundError("Dataset not found")
        
        with pytest.raises(FileNotFoundError):
            validate_property_count()

class TestUpdatePropertiesStatus:
    """Tests for the update_properties_status function."""
    
    def test_updates_status_on_success(self, tmp_path):
        """Test that status file is updated when validation passes."""
        config_mock = MagicMock()
        config_mock.state_dir = str(tmp_path / "state")
        
        with patch('validate_properties.get_config', return_value=config_mock):
            update_properties_status(property_count=20, success=True)
        
        status_file = tmp_path / "state" / "properties_status.json"
        assert status_file.exists()
        
        with open(status_file) as f:
            data = json.load(f)
        
        assert data['property_count'] == 20
        assert data['validation_passed'] is True
        assert data['minimum_required'] == MIN_PROPERTIES_REQUIRED
    
    def test_does_not_update_on_failure(self, tmp_path):
        """Test that status file is NOT updated when validation fails."""
        config_mock = MagicMock()
        config_mock.state_dir = str(tmp_path / "state")
        
        with patch('validate_properties.get_config', return_value=config_mock):
            update_properties_status(property_count=10, success=False)
        
        status_file = tmp_path / "state" / "properties_status.json"
        assert not status_file.exists()

class TestIntegration:
    """Integration tests for the full validation flow."""
    
    def test_full_validation_with_15_properties(self, tmp_path):
        """Test full validation flow with exactly 15 properties."""
        # Create test data with 15 properties
        data = {
            'material_id': [f'mat{i}' for i in range(100)],
            'composition': ['Fe2O3'] * 100,
        }
        # Add 15 property columns
        for i in range(15):
            data[f'property_{i}'] = np.random.rand(100)
        
        df = pd.DataFrame(data)
        
        # Save as parquet
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        parquet_path = processed_dir / "materials_master.parquet"
        df.to_parquet(parquet_path)
        
        # Mock config
        config_mock = MagicMock()
        config_mock.data_dir = str(tmp_path)
        config_mock.state_dir = str(tmp_path / "state")
        
        with patch('validate_properties.get_config', return_value=config_mock):
            result = validate_property_count()
        
        assert result is True
        
        # Verify status file was created
        status_file = tmp_path / "state" / "properties_status.json"
        assert status_file.exists()
        
        with open(status_file) as f:
            data = json.load(f)
        
        assert data['property_count'] == 15
        assert data['validation_passed'] is True
    
    def test_full_validation_with_14_properties(self, tmp_path):
        """Test full validation flow with 14 properties (should fail)."""
        # Create test data with 14 properties
        data = {
            'material_id': [f'mat{i}' for i in range(100)],
            'composition': ['Fe2O3'] * 100,
        }
        # Add 14 property columns
        for i in range(14):
            data[f'property_{i}'] = np.random.rand(100)
        
        df = pd.DataFrame(data)
        
        # Save as parquet
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        parquet_path = processed_dir / "materials_master.parquet"
        df.to_parquet(parquet_path)
        
        # Mock config
        config_mock = MagicMock()
        config_mock.data_dir = str(tmp_path)
        config_mock.state_dir = str(tmp_path / "state")
        
        with patch('validate_properties.get_config', return_value=config_mock):
            with pytest.raises(ValueError, match="CRITICAL: Property count"):
                validate_property_count()
        
        # Verify status file was NOT created
        status_file = tmp_path / "state" / "properties_status.json"
        assert not status_file.exists()