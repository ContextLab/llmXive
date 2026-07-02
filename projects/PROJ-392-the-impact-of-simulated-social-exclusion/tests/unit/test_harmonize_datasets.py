"""
Unit tests for code/data_download/harmonize_datasets.py

These tests verify the harmonization logic without requiring real data downloads.
"""

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the function to test
# Adjust import path based on project structure
try:
    from code.data_download.harmonize_datasets import (
        harmonize_datasets, 
        map_conditions, 
        load_dataset_metadata,
        DATASET_IDS
    )
except ImportError:
    # Fallback for different execution contexts
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
    from data_download.harmonize_datasets import (
        harmonize_datasets, 
        map_conditions, 
        load_dataset_metadata,
        DATASET_IDS
    )


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure simulating raw-fmri."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        # Create ds000246 (Exclusion)
        ds_excl = base / 'ds000246'
        ds_excl.mkdir()
        (ds_excl / 'participants.tsv').write_text(
            "participant_id\tage\tsex\n"
            "1\t25\tF\n"
            "2\t30\tM\n"
        )
        func_dir = ds_excl / 'sub-1' / 'func'
        func_dir.mkdir(parents=True)
        (func_dir / 'task-exclusion_events.tsv').write_text(
            "onset\tduration\ttrial_type\n"
            "0\t2\texclusion\n"
            "5\t2\tinclusion\n"
        )
        
        # Create ds004738 (Reward)
        ds_rew = base / 'ds004738'
        ds_rew.mkdir()
        (ds_rew / 'participants.tsv').write_text(
            "participant_id\tage\tsex\n"
            "1\t22\tF\n"
            "2\t28\tM\n"
        )
        func_dir_rew = ds_rew / 'sub-1' / 'func'
        func_dir_rew.mkdir(parents=True)
        (func_dir_rew / 'task-reward_events.tsv').write_text(
            "onset\tduration\ttrial_type\n"
            "0\t2\treward\n"
            "5\t2\tanticipation\n"
            "10\t2\tneutral\n"
        )
        
        yield base

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_map_conditions():
    """Test condition label mapping."""
    assert map_conditions('exclusion', 'ds000246') == 'social_exclusion'
    assert map_conditions('inclusion', 'ds000246') == 'social_inclusion'
    assert map_conditions('reward', 'ds004738') == 'reward_receipt'
    assert map_conditions('anticipation', 'ds004738') == 'reward_anticipation'
    assert map_conditions('NEUTRAL', 'ds004738') == 'neutral'
    assert map_conditions('unknown_label', 'ds000246') == 'unknown'

def test_harmonize_datasets_creates_files(temp_data_dir, temp_output_dir):
    """Test that harmonize_datasets creates the expected output files."""
    harmonize_datasets(temp_data_dir, temp_output_dir)
    
    assert (temp_output_dir / 'participants_harmonized.tsv').exists()
    assert (temp_output_dir / 'condition_mapping_summary.json').exists()

def test_harmonize_datasets_content(temp_data_dir, temp_output_dir):
    """Test the content of the harmonized file."""
    harmonize_datasets(temp_data_dir, temp_output_dir)
    
    df = pd.read_csv(temp_output_dir / 'participants_harmonized.tsv', sep='\t')
    
    # Check columns
    required_cols = ['participant_id', 'source_dataset', 'task_type', 'group', 'primary_condition', 'dataset_covariate']
    assert all(col in df.columns for col in required_cols)
    
    # Check row count (2 from each dataset)
    assert len(df) == 4
    
    # Check dataset distribution
    assert df['source_dataset'].value_counts()['ds000246'] == 2
    assert df['source_dataset'].value_counts()['ds004738'] == 2
    
    # Check condition mapping
    assert all(df[df['source_dataset'] == 'ds000246']['primary_condition'] == 'social_exclusion')
    assert all(df[df['source_dataset'] == 'ds004738']['primary_condition'] == 'reward_receipt')
    
    # Check covariate tag
    assert all(df['dataset_covariate'].isin(['ds000246', 'ds004738']))

def test_harmonize_datasets_missing_dir(temp_output_dir):
    """Test behavior when input directory is missing."""
    with pytest.raises(SystemExit) as exc_info:
        harmonize_datasets(Path('/nonexistent/path'), temp_output_dir)
    assert exc_info.value.code == 1

def test_condition_mapping_summary(temp_data_dir, temp_output_dir):
    """Test that condition mapping summary is generated correctly."""
    harmonize_datasets(temp_data_dir, temp_output_dir)
    
    with open(temp_output_dir / 'condition_mapping_summary.json') as f:
        mapping = json.load(f)
    
    assert isinstance(mapping, list)
    assert len(mapping) > 0
    
    # Check structure
    first_item = mapping[0]
    assert 'dataset_id' in first_item
    assert 'original_label' in first_item
    assert 'mapped_label' in first_item
    
    # Check specific mappings
    mapped_labels = [m['mapped_label'] for m in mapping]
    assert 'social_exclusion' in mapped_labels
    assert 'reward_receipt' in mapped_labels
    assert 'reward_anticipation' in mapped_labels