"""
Tests for data splitting functionality in preprocess.py
"""

import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path

from src.data.preprocess import (
    load_interactions,
    filter_unknown_labels,
    load_valid_pathogens,
    split_pathogen_stratified,
    save_split_metadata,
    run_preprocessing_pipeline
)

@pytest.fixture
def sample_interactions():
    """Create sample interaction data"""
    data = {
        'pathogen_id': ['P1', 'P1', 'P1', 'P2', 'P2', 'P3', 'P3', 'P3', 'P3', 'P4', 'P4', 'P5', 'P5', 'P5', 'P5', 'P5', 'P6', 'P6', 'P7', 'P7', 'P8', 'P8', 'P8', 'P9', 'P9', 'P9', 'P9', 'P10', 'P10', 'P10', 'P11', 'P11', 'P12', 'P12', 'P12', 'P13', 'P13', 'P14', 'P14', 'P14', 'P15', 'P15', 'P15', 'P16', 'P16', 'P17', 'P17', 'P18', 'P18', 'P19', 'P19', 'P20', 'P20'],
        'host_id': ['H1', 'H2', 'H3', 'H1', 'H4', 'H1', 'H2', 'H3', 'H5', 'H1', 'H2', 'H1', 'H2', 'H3', 'H4', 'H5', 'H1', 'H2', 'H1', 'H2', 'H1', 'H2', 'H3', 'H1', 'H2', 'H3', 'H4', 'H1', 'H2', 'H3', 'H1', 'H2', 'H1', 'H2', 'H3', 'H1', 'H2', 'H1', 'H2', 'H3', 'H1', 'H2', 'H3', 'H1', 'H2', 'H1', 'H2', 'H1', 'H2', 'H1', 'H2', 'H1', 'H2'],
        'interaction_type': ['positive', 'positive', 'negative', 'positive', 'negative', 'positive', 'negative', 'positive', 'negative', 'positive', 'negative', 'positive', 'negative', 'positive', 'negative', 'positive', 'positive', 'negative', 'positive', 'negative', 'positive', 'negative', 'positive', 'positive', 'negative', 'positive', 'negative', 'positive', 'negative', 'positive', 'positive', 'negative', 'positive', 'negative', 'positive', 'positive', 'negative', 'positive', 'negative', 'positive', 'positive', 'negative', 'positive', 'positive', 'negative', 'positive', 'negative', 'positive', 'negative', 'positive', 'negative', 'positive', 'negative']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_valid_pathogens():
    """Create list of valid pathogen IDs"""
    return ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P16', 'P17', 'P18', 'P19', 'P20']

@pytest.fixture
def temp_files(sample_interactions, sample_valid_pathogens):
    """Create temporary files for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Save interactions
        interactions_file = tmpdir_path / 'interactions.csv'
        sample_interactions.to_csv(interactions_file, index=False)
        
        # Save valid pathogens
        valid_pathogens_file = tmpdir_path / 'valid_pathogens.json'
        with open(valid_pathogens_file, 'w') as f:
            json.dump(sample_valid_pathogens, f)
        
        yield {
            'interactions': str(interactions_file),
            'valid_pathogens': str(valid_pathogens_file),
            'output_dir': str(tmpdir_path / 'output')
        }

def test_load_interactions(temp_files):
    """Test loading interaction data"""
    df = load_interactions(temp_files['interactions'])
    assert len(df) == 52
    assert 'pathogen_id' in df.columns
    assert 'host_id' in df.columns
    assert 'interaction_type' in df.columns

def test_filter_unknown_labels(temp_files):
    """Test filtering unknown labels"""
    df = load_interactions(temp_files['interactions'])
    
    # Add some unknown labels
    df_with_unknown = df.copy()
    df_with_unknown.loc[0, 'interaction_type'] = 'unknown'
    df_with_unknown.loc[10, 'interaction_type'] = 'unknown'
    
    df_filtered = filter_unknown_labels(df_with_unknown)
    assert len(df_filtered) == len(df_with_unknown) - 2
    assert 'unknown' not in df_filtered['interaction_type'].values

def test_load_valid_pathogens(temp_files):
    """Test loading valid pathogen list"""
    pathogens = load_valid_pathogens(temp_files['valid_pathogens'])
    assert len(pathogens) == 20
    assert 'P1' in pathogens
    assert 'P20' in pathogens

def test_split_pathogen_stratified(temp_files):
    """Test pathogen-stratified splitting"""
    df = load_interactions(temp_files['interactions'])
    valid_pathogens = load_valid_pathogens(temp_files['valid_pathogens'])
    
    train_df, val_df, holdout_df = split_pathogen_stratified(
        df,
        valid_pathogens,
        test_size=0.2,
        val_size=0.1,
        random_state=42,
        holdout_size=5
    )
    
    # Check that sets are non-overlapping
    train_pathogens = set(train_df['pathogen_id'].unique())
    val_pathogens = set(val_df['pathogen_id'].unique())
    holdout_pathogens = set(holdout_df['pathogen_id'].unique())
    
    assert len(train_pathogens & val_pathogens) == 0
    assert len(train_pathogens & holdout_pathogens) == 0
    assert len(val_pathogens & holdout_pathogens) == 0
    
    # Check holdout size
    assert len(holdout_pathogens) == 5
    
    # Check that all sets have records
    assert len(train_df) > 0
    assert len(val_df) > 0
    assert len(holdout_df) > 0

def test_save_split_metadata(temp_files, sample_interactions):
    """Test saving split metadata"""
    df = load_interactions(temp_files['interactions'])
    valid_pathogens = load_valid_pathogens(temp_files['valid_pathogens'])
    
    train_df, val_df, holdout_df = split_pathogen_stratified(
        df, valid_pathogens, holdout_size=5, random_state=42
    )
    
    save_split_metadata(train_df, val_df, holdout_df, temp_files['output_dir'])
    
    metadata_file = Path(temp_files['output_dir']) / 'split_metadata.json'
    assert metadata_file.exists()
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    assert 'train' in metadata
    assert 'val' in metadata
    assert 'holdout' in metadata
    assert metadata['train']['pathogen_count'] == len(train_df['pathogen_id'].unique())

def test_run_preprocessing_pipeline(temp_files):
    """Test complete preprocessing pipeline"""
    train_df, val_df, holdout_df = run_preprocessing_pipeline(
        temp_files['interactions'],
        temp_files['valid_pathogens'],
        temp_files['output_dir'],
        random_state=42,
        holdout_size=5
    )
    
    # Check output files exist
    output_path = Path(temp_files['output_dir'])
    assert (output_path / 'train_interactions.csv').exists()
    assert (output_path / 'val_interactions.csv').exists()
    assert (output_path / 'holdout_interactions.csv').exists()
    assert (output_path / 'split_metadata.json').exists()
    
    # Check data integrity
    assert len(train_df) + len(val_df) + len(holdout_df) == 52
    
    # Check non-overlapping pathogens
    train_pathogens = set(train_df['pathogen_id'].unique())
    val_pathogens = set(val_df['pathogen_id'].unique())
    holdout_pathogens = set(holdout_df['pathogen_id'].unique())
    
    assert len(train_pathogens & val_pathogens) == 0
    assert len(train_pathogens & holdout_pathogens) == 0
    assert len(val_pathogens & holdout_pathogens) == 0

def test_split_with_insufficient_pathogens(temp_files, sample_interactions):
    """Test error when not enough pathogens for holdout"""
    df = load_interactions(temp_files['interactions'])
    valid_pathogens = ['P1', 'P2', 'P3']  # Only 3 pathogens
    
    with pytest.raises(ValueError, match="Not enough unique pathogens"):
        split_pathogen_stratified(
            df,
            valid_pathogens,
            holdout_size=5,
            random_state=42
        )