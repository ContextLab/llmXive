"""
Tests for the VR mapping logging functionality in preprocess.py.

These tests verify that:
1. The VR mapping log file is created
2. Mapping decisions are correctly logged
3. The log format is consistent
"""

import pytest
import os
import sys
import json
from pathlib import Path
import pandas as pd
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.data.preprocess import (
    load_merged_data,
    load_blend_shape_config,
    assign_salience_level,
    map_to_blend_shapes,
    process_salience_mapping,
    run_preprocessing_pipeline
)
from code.utils.logging_utils import get_vr_mapping_log_path, log_vr_mapping
from code.config import ensure_directories


@pytest.fixture
def sample_config():
    """Sample blend shape configuration."""
    return {
        'story_to_salience': {
            'story_001': 'high',
            'story_002': 'low',
            'story_003': 'high'
        },
        'blend_shapes': {
            'high': {
                'jawOpen': 0.8,
                'mouthClose': 0.2,
                'eyeBlinkLeft': 0.1,
                'eyeBlinkRight': 0.1
            },
            'low': {
                'jawOpen': 0.2,
                'mouthClose': 0.8,
                'eyeBlinkLeft': 0.0,
                'eyeBlinkRight': 0.0
            }
        },
        'default_blend_shapes': {
            'jawOpen': 0.0,
            'mouthClose': 0.0
        }
    }

@pytest.fixture
def sample_dataframe():
    """Sample merged DataFrame."""
    return pd.DataFrame({
        'story_id': ['story_001', 'story_002', 'story_003', 'story_999'],
        'mfq_score': [3.5, 2.1, 4.0, 1.5],
        'judgment': [1, 0, 1, 0]
    })

@pytest.fixture
def log_path(tmp_path):
    """Temporary log path for testing."""
    log_dir = tmp_path / 'data' / 'logs'
    log_dir.mkdir(parents=True)
    return log_dir / 'vr_mapping.log'

def test_assign_salience_level_known_story(sample_config):
    """Test that known stories get the correct salience level."""
    assert assign_salience_level('story_001', sample_config) == 'high'
    assert assign_salience_level('story_002', sample_config) == 'low'
    assert assign_salience_level('story_003', sample_config) == 'high'

def test_assign_salience_level_unknown_story(sample_config):
    """Test that unknown stories default to 'low'."""
    assert assign_salience_level('story_unknown', sample_config) == 'low'

def test_map_to_blend_shapes_high_salience(sample_config):
    """Test mapping for high salience stories."""
    blend_shapes = map_to_blend_shapes('story_001', sample_config)
    assert blend_shapes['jawOpen'] == 0.8
    assert blend_shapes['mouthClose'] == 0.2

def test_map_to_blend_shapes_low_salience(sample_config):
    """Test mapping for low salience stories."""
    blend_shapes = map_to_blend_shapes('story_002', sample_config)
    assert blend_shapes['jawOpen'] == 0.2
    assert blend_shapes['mouthClose'] == 0.8

def test_log_vr_mapping_creates_file(tmp_path):
    """Test that log_vr_mapping creates the log file."""
    log_file = tmp_path / 'test_vr_mapping.log'
    
    log_vr_mapping(
        story_id='test_001',
        salience_level='high',
        blend_shapes={'jawOpen': 0.8},
        log_path=log_file
    )
    
    assert log_file.exists()
    with open(log_file, 'r') as f:
        content = f.read()
        assert 'test_001' in content
        assert 'high' in content

def test_process_salience_mapping_logs_all_rows(sample_config, sample_dataframe, tmp_path):
    """Test that process_salience_mapping logs every row."""
    log_file = tmp_path / 'data' / 'logs' / 'vr_mapping.log'
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    df, logs = process_salience_mapping(sample_dataframe, sample_config, log_file)
    
    # Check that all rows were processed
    assert len(logs) == len(sample_dataframe)
    
    # Check that log file exists and has content
    assert log_file.exists()
    with open(log_file, 'r') as f:
        lines = f.readlines()
        assert len(lines) == len(sample_dataframe)
        
        # Verify each story_id is logged
        logged_ids = [line for line in lines if 'STORY_ID=' in line]
        assert len(logged_ids) == len(sample_dataframe)

def test_preprocessing_pipeline_creates_log_file(sample_config, sample_dataframe, tmp_path):
    """Test that the full pipeline creates the VR mapping log."""
    # Create temp directories
    data_dir = tmp_path / 'data' / 'processed'
    data_dir.mkdir(parents=True)
    
    config_file = tmp_path / 'data' / 'config' / 'unity_blend_shapes.yaml'
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    import yaml
    with open(config_file, 'w') as f:
        yaml.dump(sample_config, f)
    
    merged_file = data_dir / 'merged_dataset.csv'
    sample_dataframe.to_csv(merged_file, index=False)
    
    output_file = data_dir / 'preprocessed_dataset.csv'
    
    # Run pipeline
    with patch('code.data.preprocess.ensure_directories'):
        with patch('code.data.preprocess.get_vr_mapping_log_path', return_value=tmp_path / 'data' / 'logs' / 'vr_mapping.log'):
            df = run_preprocessing_pipeline(merged_file, config_file, output_file)
    
    # Verify log file was created
    log_file = tmp_path / 'data' / 'logs' / 'vr_mapping.log'
    assert log_file.exists()
    
    # Verify output file was created
    assert output_file.exists()
    assert len(pd.read_csv(output_file)) == len(sample_dataframe)