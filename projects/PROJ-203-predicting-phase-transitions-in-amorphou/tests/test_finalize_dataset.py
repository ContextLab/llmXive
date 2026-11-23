"""
Tests for code/data/finalize_dataset.py (T014)
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.finalize_dataset import (
    load_temp_dataset,
    load_simulation_metadata,
    enrich_with_metadata,
    validate_final_dataset,
    save_final_dataset
)
from config import get_data_config, reset_config

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def setup_test_data(temp_dir):
    # Mock config to use temp_dir
    # We cannot easily mock the global config, so we will test functions
    # that take paths or data directly, or mock the file existence.
    
    # Create mock temp dataset
    processed_dir = temp_dir / "processed"
    processed_dir.mkdir()
    
    df_temp = pd.DataFrame({
        'composition_id': ['A', 'B', 'C'],
        'Tg': [500.0, 600.0, 550.0],
        'label': [1, 0, 1],
        'rdf_peak': [3.4, 3.5, 3.45]
    })
    temp_file = processed_dir / "labeled_dataset_temp.parquet"
    df_temp.to_parquet(temp_file)
    
    # Create mock metadata
    metadata = {
        'A': {'status': 'success', 'cooling_rate': 1e10},
        'B': {'status': 'truncated', 'cooling_rate': 1e10},
        'C': {'status': 'failed', 'cooling_rate': 1e10}
    }
    meta_file = processed_dir / "simulation_metadata.json"
    with open(meta_file, 'w') as f:
        json.dump(metadata, f)
        
    return processed_dir, df_temp

def test_enrich_with_metadata(setup_test_data):
    processed_dir, df_temp = setup_test_data
    
    # Load metadata manually to pass to function
    meta_file = processed_dir / "simulation_metadata.json"
    with open(meta_file, 'r') as f:
        metadata = json.load(f)
    
    # Enrich
    df_enriched = enrich_with_metadata(df_temp.copy(), metadata)
    
    # Assertions
    assert 'simulation_status' in df_enriched.columns
    assert 'cooling_rate' in df_enriched.columns
    
    assert df_enriched.loc[df_enriched['composition_id'] == 'A', 'simulation_status'].iloc[0] == 'success'
    assert df_enriched.loc[df_enriched['composition_id'] == 'B', 'simulation_status'].iloc[0] == 'truncated'
    assert df_enriched.loc[df_enriched['composition_id'] == 'C', 'simulation_status'].iloc[0] == 'failed'
    
    assert df_enriched.loc[df_enriched['composition_id'] == 'A', 'cooling_rate'].iloc[0] == 1e10

def test_validate_final_dataset():
    df = pd.DataFrame({
        'composition_id': ['A'],
        'simulation_status': ['success'],
        'cooling_rate': [1e10]
    })
    assert validate_final_dataset(df) is True
    
    # Missing column
    df_bad = pd.DataFrame({
        'composition_id': ['A'],
        'simulation_status': ['success']
    })
    with pytest.raises(ValueError):
        validate_final_dataset(df_bad)

def test_save_final_dataset(temp_dir):
    df = pd.DataFrame({
        'composition_id': ['A'],
        'simulation_status': ['success'],
        'cooling_rate': [1e10]
    })
    output_path = temp_dir / "final_dataset.parquet"
    
    save_final_dataset(df, output_path)
    
    assert output_path.exists()
    df_loaded = pd.read_parquet(output_path)
    assert len(df_loaded) == 1
    assert 'simulation_status' in df_loaded.columns
