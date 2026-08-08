import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
import json
from datetime import datetime

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.preprocess import generate_provenance, load_ebird_data

@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_generate_provenance_basic(temp_data_dir):
    """Test basic provenance generation."""
    # Create sample processed data
    processed_df = pd.DataFrame({
        'species': ['Species_A', 'Species_B'],
        'grid_cell': [100, 200],
        'year': [2020, 2021],
        'week': [10, 15],
        'checklist_id': ['check_001', 'check_002'],
        'phenology_metric': [1.5, 2.0]
    })
    
    # Create sample raw data
    raw_df = pd.DataFrame({
        'species': ['Species_A', 'Species_B'],
        'lat': [40.0, 45.0],
        'lon': [-75.0, -80.0],
        'date': ['2020-03-15', '2021-04-20'],
        'count': [5, 10],
        'checklist_id': ['check_001', 'check_002']
    })
    
    # Output path
    output_path = temp_data_dir / "row_mapping.json"
    
    # Generate provenance
    generate_provenance(processed_df, raw_df, str(output_path))
    
    # Verify file exists
    assert output_path.exists(), "Provenance mapping file not created"
    
    # Verify JSON content
    with open(output_path, 'r') as f:
        mapping = json.load(f)
    
    assert len(mapping) == 2, "Mapping should have 2 entries"
    assert mapping[0]['species'] == 'Species_A'
    assert mapping[0]['original_checklist_id'] == 'check_001'
    assert mapping[1]['original_checklist_id'] == 'check_002'

def test_generate_provenance_integrity_check(temp_data_dir):
    """Test that provenance verifies checklist_id integrity."""
    # Create processed data with checklist_id
    processed_df = pd.DataFrame({
        'species': ['Species_A'],
        'grid_cell': [100],
        'year': [2020],
        'week': [10],
        'checklist_id': ['check_valid']
    })
    
    # Create raw data with matching checklist_id
    raw_df = pd.DataFrame({
        'species': ['Species_A'],
        'lat': [40.0],
        'lon': [-75.0],
        'date': ['2020-03-15'],
        'count': [5],
        'checklist_id': ['check_valid']
    })
    
    output_path = temp_data_dir / "row_mapping.json"
    generate_provenance(processed_df, raw_df, str(output_path))
    
    assert output_path.exists()

def test_generate_provenance_missing_checklist_id(temp_data_dir):
    """Test provenance handling when checklist_id is missing in raw data."""
    processed_df = pd.DataFrame({
        'species': ['Species_A'],
        'grid_cell': [100],
        'year': [2020],
        'week': [10],
        'checklist_id': ['check_missing']
    })
    
    # Raw data does NOT contain 'check_missing'
    raw_df = pd.DataFrame({
        'species': ['Species_B'],
        'lat': [45.0],
        'lon': [-80.0],
        'date': ['2021-04-20'],
        'count': [10],
        'checklist_id': ['check_other']
    })
    
    output_path = temp_data_dir / "row_mapping.json"
    generate_provenance(processed_df, raw_df, str(output_path))
    
    # Should still create file, but log warning (not tested here)
    assert output_path.exists()

def test_generate_provenance_empty_processed(temp_data_dir):
    """Test provenance generation with empty processed dataframe."""
    processed_df = pd.DataFrame(columns=['species', 'grid_cell', 'year', 'week', 'checklist_id'])
    raw_df = pd.DataFrame({
        'species': ['Species_A'],
        'lat': [40.0],
        'lon': [-75.0],
        'date': ['2020-03-15'],
        'count': [5],
        'checklist_id': ['check_001']
    })
    
    output_path = temp_data_dir / "row_mapping.json"
    generate_provenance(processed_df, raw_df, str(output_path))
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        mapping = json.load(f)
    assert len(mapping) == 0

def test_generate_provenance_output_schema(temp_data_dir):
    """Test that output JSON has correct schema."""
    processed_df = pd.DataFrame({
        'species': ['Species_A'],
        'grid_cell': [100],
        'year': [2020],
        'week': [10],
        'checklist_id': ['check_001']
    })
    
    raw_df = pd.DataFrame({
        'species': ['Species_A'],
        'lat': [40.0],
        'lon': [-75.0],
        'date': ['2020-03-15'],
        'count': [5],
        'checklist_id': ['check_001']
    })
    
    output_path = temp_data_dir / "row_mapping.json"
    generate_provenance(processed_df, raw_df, str(output_path))
    
    with open(output_path, 'r') as f:
        mapping = json.load(f)
    
    # Check required keys
    required_keys = ['processed_row_idx', 'species', 'grid_cell', 'year', 'week', 'original_checklist_id']
    for entry in mapping:
        for key in required_keys:
            assert key in entry, f"Missing key: {key}"