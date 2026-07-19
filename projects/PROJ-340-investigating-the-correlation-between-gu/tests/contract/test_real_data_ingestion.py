"""
Contract test for real-data ingestion (US4).

This test validates that the real data ingestion pipeline correctly:
1. Identifies the data source type (real vs synthetic)
2. Validates required variables against the schema
3. Handles missing variables with specific error messages
4. Produces a valid ingestion report structure
"""
import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingest import load_schema, validate_variables, load_data
from config import load_config


class TestRealDataIngestionContract:
    """Contract tests for real-data ingestion functionality."""

    @pytest.fixture
    def mock_real_dataset(self):
        """Create a mock real dataset with expected columns."""
        # Simulate a real dataset with gut microbiome taxa and sleep metrics
        data = {
            'sample_id': [f'sample_{i}' for i in range(100)],
            'Bacteroides': np.random.randint(0, 1000, 100),
            'Firmicutes': np.random.randint(0, 1000, 100),
            'Actinobacteria': np.random.randint(0, 1000, 100),
            'Proteobacteria': np.random.randint(0, 1000, 100),
            'SWS duration': np.random.uniform(60, 120, 100),
            'REM duration': np.random.uniform(90, 150, 100),
            'Total sleep time': np.random.uniform(400, 500, 100),
            'Sleep efficiency': np.random.uniform(0.75, 0.95, 100),
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def mock_schema(self):
        """Create a mock schema definition."""
        return {
            'predictors': {
                'taxa': ['Bacteroides', 'Firmicutes', 'Actinobacteria', 'Proteobacteria']
            },
            'outcomes': {
                'sleep_metrics': ['SWS duration', 'REM duration', 'Total sleep time', 'Sleep efficiency']
            }
        }

    def test_schema_loading(self, mock_schema, tmp_path):
        """Test that schema can be loaded and validated."""
        schema_path = tmp_path / "dataset.schema.yaml"
        import yaml
        with open(schema_path, 'w') as f:
            yaml.dump(mock_schema, f)
        
        loaded_schema = load_schema(str(schema_path))
        assert 'predictors' in loaded_schema
        assert 'outcomes' in loaded_schema
        assert len(loaded_schema['predictors']['taxa']) > 0
        assert len(loaded_schema['outcomes']['sleep_metrics']) > 0

    def test_variable_validation_complete(self, mock_real_dataset, mock_schema, tmp_path):
        """Test validation passes when all required variables are present."""
        # Write mock schema
        schema_path = tmp_path / "dataset.schema.yaml"
        import yaml
        with open(schema_path, 'w') as f:
            yaml.dump(mock_schema, f)
        
        # Write mock data
        data_path = tmp_path / "real_data.csv"
        mock_real_dataset.to_csv(data_path, index=False)
        
        # Validate
        metrics = validate_variables(str(data_path), str(schema_path))
        
        assert metrics['success'] is True
        assert metrics['predictor_percentage'] == 100.0
        assert metrics['outcome_percentage'] == 100.0
        assert metrics['missing_predictors'] == []
        assert metrics['missing_outcomes'] == []

    def test_variable_validation_missing_predictors(self, mock_real_dataset, mock_schema, tmp_path):
        """Test validation fails when predictor variables are missing."""
        # Remove a predictor column
        incomplete_data = mock_real_dataset.drop(columns=['Bacteroides'])
        
        # Write mock schema
        schema_path = tmp_path / "dataset.schema.yaml"
        import yaml
        with open(schema_path, 'w') as f:
            yaml.dump(mock_schema, f)
        
        # Write incomplete data
        data_path = tmp_path / "incomplete_data.csv"
        incomplete_data.to_csv(data_path, index=False)
        
        # Validate
        metrics = validate_variables(str(data_path), str(schema_path))
        
        assert metrics['success'] is False
        assert 'Bacteroides' in metrics['missing_predictors']
        assert metrics['predictor_percentage'] < 100.0

    def test_variable_validation_missing_outcomes(self, mock_real_dataset, mock_schema, tmp_path):
        """Test validation fails when outcome variables are missing."""
        # Remove an outcome column
        incomplete_data = mock_real_dataset.drop(columns=['SWS duration'])
        
        # Write mock schema
        schema_path = tmp_path / "dataset.schema.yaml"
        import yaml
        with open(schema_path, 'w') as f:
            yaml.dump(mock_schema, f)
        
        # Write incomplete data
        data_path = tmp_path / "incomplete_data.csv"
        incomplete_data.to_csv(data_path, index=False)
        
        # Validate
        metrics = validate_variables(str(data_path), str(schema_path))
        
        assert metrics['success'] is False
        assert 'SWS duration' in metrics['missing_outcomes']
        assert metrics['outcome_percentage'] < 100.0

    def test_data_loading_with_real_source(self, mock_real_dataset, mock_schema, tmp_path):
        """Test that data loading works with real data source."""
        # Write mock schema
        schema_path = tmp_path / "dataset.schema.yaml"
        import yaml
        with open(schema_path, 'w') as f:
            yaml.dump(mock_schema, f)
        
        # Write mock data
        data_path = tmp_path / "real_data.csv"
        mock_real_dataset.to_csv(data_path, index=False)
        
        # Load data
        loaded_df = load_data(str(data_path), str(schema_path))
        
        assert loaded_df is not None
        assert len(loaded_df) == 100
        assert 'sample_id' in loaded_df.columns
        assert 'Bacteroides' in loaded_df.columns
        assert 'SWS duration' in loaded_df.columns

    def test_data_loading_fails_on_missing_variables(self, mock_real_dataset, mock_schema, tmp_path):
        """Test that data loading fails with specific error when variables are missing."""
        # Remove a required column
        incomplete_data = mock_real_dataset.drop(columns=['Firmicutes'])
        
        # Write mock schema
        schema_path = tmp_path / "dataset.schema.yaml"
        import yaml
        with open(schema_path, 'w') as f:
            yaml.dump(mock_schema, f)
        
        # Write incomplete data
        data_path = tmp_path / "incomplete_data.csv"
        incomplete_data.to_csv(data_path, index=False)
        
        # Test that load_data raises SystemExit
        with pytest.raises(SystemExit) as exc_info:
            load_data(str(data_path), str(schema_path))
        
        assert exc_info.value.code == 1

    def test_ingestion_report_structure(self, mock_real_dataset, mock_schema, tmp_path):
        """Test that ingestion produces a report with required structure."""
        # Write mock schema
        schema_path = tmp_path / "dataset.schema.yaml"
        import yaml
        with open(schema_path, 'w') as f:
            yaml.dump(mock_schema, f)
        
        # Write mock data
        data_path = tmp_path / "real_data.csv"
        mock_real_dataset.to_csv(data_path, index=False)
        
        # Validate
        metrics = validate_variables(str(data_path), str(schema_path))
        
        # Check report structure
        required_fields = [
            'success', 'total_predictors', 'loaded_predictors', 
            'predictor_percentage', 'missing_predictors',
            'total_outcomes', 'loaded_outcomes', 'outcome_percentage',
            'missing_outcomes', 'data_source_type'
        ]
        
        for field in required_fields:
            assert field in metrics, f"Missing required field: {field}"
        
        # Check data source type
        assert metrics['data_source_type'] == 'real'

    def test_real_data_vs_synthetic_distinction(self, mock_real_dataset, mock_schema, tmp_path):
        """Test that the system distinguishes between real and synthetic data sources."""
        # Write mock schema
        schema_path = tmp_path / "dataset.schema.yaml"
        import yaml
        with open(schema_path, 'w') as f:
            yaml.dump(mock_schema, f)
        
        # Write mock data (simulating real data)
        data_path = tmp_path / "real_data.csv"
        mock_real_dataset.to_csv(data_path, index=False)
        
        # Validate
        metrics = validate_variables(str(data_path), str(schema_path))
        
        assert metrics['data_source_type'] == 'real'
        assert 'synthetic' not in str(data_path).lower()

    def test_error_message_clarity(self, mock_real_dataset, mock_schema, tmp_path):
        """Test that error messages are clear and specific."""
        # Remove a specific column
        incomplete_data = mock_real_dataset.drop(columns=['Sleep efficiency'])
        
        # Write mock schema
        schema_path = tmp_path / "dataset.schema.yaml"
        import yaml
        with open(schema_path, 'w') as f:
            yaml.dump(mock_schema, f)
        
        # Write incomplete data
        data_path = tmp_path / "incomplete_data.csv"
        incomplete_data.to_csv(data_path, index=False)
        
        # Validate
        metrics = validate_variables(str(data_path), str(schema_path))
        
        assert metrics['success'] is False
        assert 'Sleep efficiency' in metrics['missing_outcomes']
        assert len(metrics['missing_outcomes']) == 1

    def test_percentage_calculation_accuracy(self, mock_real_dataset, mock_schema, tmp_path):
        """Test that percentage calculations are accurate."""
        # Remove half of the predictors
        incomplete_data = mock_real_dataset.drop(columns=['Bacteroides', 'Firmicutes'])
        
        # Write mock schema
        schema_path = tmp_path / "dataset.schema.yaml"
        import yaml
        with open(schema_path, 'w') as f:
            yaml.dump(mock_schema, f)
        
        # Write incomplete data
        data_path = tmp_path / "incomplete_data.csv"
        incomplete_data.to_csv(data_path, index=False)
        
        # Validate
        metrics = validate_variables(str(data_path), str(schema_path))
        
        # Should have 2 out of 4 predictors (50%)
        assert metrics['predictor_percentage'] == 50.0
        assert metrics['total_predictors'] == 4
        assert metrics['loaded_predictors'] == 2
        assert len(metrics['missing_predictors']) == 2