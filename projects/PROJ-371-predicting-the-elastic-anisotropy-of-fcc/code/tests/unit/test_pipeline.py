"""
Unit tests for the pipeline orchestration script.
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest
import pandas as pd
import json

from src.cli.run_pipeline import main, validate_output_descriptors
from src.utils.config import get_config

@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    return {
        "paths": {
            "raw": "/tmp/raw",
            "processed": "/tmp/processed",
            "output": "/tmp/output"
        },
        "seeds": {
            "random": 42
        },
        "api_keys": {
            "MP_API_KEY": "test_key"
        }
    }

@pytest.fixture
def sample_ingest_data():
    """Sample data simulating ingestion output."""
    return pd.DataFrame({
        'material_id': ['MP-1', 'MP-2', 'MP-3'],
        'formula': ['Al', 'Cu', 'Ni'],
        'C11': [100.0, 168.0, 246.0],
        'C12': [50.0, 121.0, 147.0],
        'C44': [28.0, 75.0, 124.0],
        'structure': [{'symmetry': {'crystal_system': 'cubic'}} for _ in range(3)]
    })

@pytest.fixture
def sample_clean_data():
    """Sample data simulating cleaning output."""
    return pd.DataFrame({
        'material_id': ['MP-1', 'MP-2', 'MP-3'],
        'formula': ['Al', 'Cu', 'Ni'],
        'C11': [100.0, 168.0, 246.0],
        'C12': [50.0, 121.0, 147.0],
        'C44': [28.0, 75.0, 124.0],
        'A1': [0.56, 1.04, 1.35],
        'element': ['Al', 'Cu', 'Ni']
    })

@pytest.fixture
def sample_feature_data():
    """Sample data simulating feature engineering output."""
    return pd.DataFrame({
        'material_id': ['MP-1', 'MP-2', 'MP-3'],
        'formula': ['Al', 'Cu', 'Ni'],
        'C11': [100.0, 168.0, 246.0],
        'C12': [50.0, 121.0, 147.0],
        'C44': [28.0, 75.0, 124.0],
        'A1': [0.56, 1.04, 1.35],
        'element': ['Al', 'Cu', 'Ni'],
        'atomic_radius_variance': [0.1, 0.2, 0.15],
        'electronegativity_std': [0.5, 0.6, 0.55],
        'valence_electron_concentration': [3.0, 11.0, 10.0]
    })

def test_pipeline_execution(mock_config, sample_feature_data, tmp_path):
    """Test that the pipeline runs end-to-end with mocked dependencies."""
    output_file = tmp_path / "elastic_anisotropy.csv"
    manifest_file = tmp_path / "manifest.json"
    
    # Create a dummy manifest
    manifest_data = {"ids": ["MP-1", "MP-2", "MP-3"]}
    with open(manifest_file, 'w') as f:
        json.dump(manifest_data, f)
    
    with patch('src.cli.run_pipeline.get_config', return_value=mock_config), \
         patch('src.cli.run_pipeline.validate_api_keys', return_value=True), \
         patch('src.cli.run_pipeline.ensure_directories'), \
         patch('src.cli.run_pipeline.ingest_elastic_data', return_value=sample_feature_data), \
         patch('src.cli.run_pipeline.clean_elastic_data', return_value=sample_feature_data), \
         patch('src.cli.run_pipeline.compute_compositional_features', return_value=sample_feature_data), \
         patch('src.cli.run_pipeline.get_path', side_effect=lambda cfg, key: str(output_file) if key == "processed_anisotropy" else str(manifest_file)):
        
        exit_code = main(["--manifest", str(manifest_file), "--output", str(output_file)])
        
        assert exit_code == 0
        assert output_file.exists()
        
        # Verify the output file content
        df = pd.read_csv(output_file)
        assert len(df) == 3
        assert 'A1' in df.columns
        assert 'atomic_radius_variance' in df.columns

def test_pipeline_empty_ingest(tmp_path):
    """Test pipeline behavior when ingestion returns empty data."""
    manifest_file = tmp_path / "manifest.json"
    output_file = tmp_path / "elastic_anisotropy.csv"
    
    manifest_data = {"ids": []}
    with open(manifest_file, 'w') as f:
        json.dump(manifest_data, f)
    
    with patch('src.cli.run_pipeline.get_config', return_value={"paths": {"raw": "/tmp"}}), \
         patch('src.cli.run_pipeline.validate_api_keys', return_value=True), \
         patch('src.cli.run_pipeline.ensure_directories'), \
         patch('src.cli.run_pipeline.ingest_elastic_data', return_value=pd.DataFrame()), \
         patch('src.cli.run_pipeline.get_path', side_effect=lambda cfg, key: str(output_file) if key == "processed_anisotropy" else str(manifest_file)):
        
        exit_code = main(["--manifest", str(manifest_file), "--output", str(output_file)])
        
        assert exit_code == 1

def test_pipeline_validation_flag(mock_config, sample_feature_data, tmp_path):
    """Test pipeline with --validate flag."""
    output_file = tmp_path / "elastic_anisotropy.csv"
    manifest_file = tmp_path / "manifest.json"
    
    manifest_data = {"ids": ["MP-1"]}
    with open(manifest_file, 'w') as f:
        json.dump(manifest_data, f)
    
    with patch('src.cli.run_pipeline.get_config', return_value=mock_config), \
         patch('src.cli.run_pipeline.validate_api_keys', return_value=True), \
         patch('src.cli.run_pipeline.ensure_directories'), \
         patch('src.cli.run_pipeline.ingest_elastic_data', return_value=sample_feature_data), \
         patch('src.cli.run_pipeline.clean_elastic_data', return_value=sample_feature_data), \
         patch('src.cli.run_pipeline.compute_compositional_features', return_value=sample_feature_data), \
         patch('src.cli.run_pipeline.get_path', side_effect=lambda cfg, key: str(output_file) if key == "processed_anisotropy" else str(manifest_file)):
        
        exit_code = main(["--manifest", str(manifest_file), "--output", str(output_file), "--validate"])
        
        assert exit_code == 0
        assert output_file.exists()
