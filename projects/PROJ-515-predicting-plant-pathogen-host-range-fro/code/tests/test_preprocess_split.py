"""
Tests for pathogen-stratified splitting functionality in preprocess.py.
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
    """Create sample interaction data."""
    data = {
        'pathogen_id': ['P1', 'P1', 'P1', 'P2', 'P2', 'P3', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P16'],
        'host_id': ['H1', 'H2', 'H3', 'H1', 'H4', 'H2', 'H5', 'H1', 'H2', 'H3', 'H4', 'H5', 'H1', 'H2', 'H3', 'H4', 'H5', 'H1', 'H2', 'H3'],
        'interaction_label': [1, 0, 1, 1, 0, 0, 1, 'unknown', 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_valid_pathogens():
    """Create sample valid pathogens list."""
    return ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P16']


@pytest.fixture
def temp_files(sample_interactions, sample_valid_pathogens):
    """Create temporary files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Save interactions
        interactions_path = tmpdir / "interactions.csv"
        sample_interactions.to_csv(interactions_path, index=False)
        
        # Save valid pathogens
        valid_pathogens_path = tmpdir / "valid_pathogens.json"
        with open(valid_pathogens_path, 'w') as f:
            json.dump(sample_valid_pathogens, f)
        
        yield {
            "interactions": str(interactions_path),
            "valid_pathogens": str(valid_pathogens_path),
            "output_dir": str(tmpdir / "output")
        }


def test_load_interactions(temp_files):
    """Test loading interactions from CSV."""
    df = load_interactions(temp_files["interactions"])
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 20
    assert 'pathogen_id' in df.columns
    assert 'host_id' in df.columns
    assert 'interaction_label' in df.columns


def test_filter_unknown_labels(sample_interactions):
    """Test filtering out unknown labels."""
    filtered = filter_unknown_labels(sample_interactions)
    assert 'unknown' not in filtered['interaction_label'].values
    assert len(filtered) < len(sample_interactions)


def test_load_valid_pathogens(temp_files):
    """Test loading valid pathogens from JSON."""
    pathogens = load_valid_pathogens(temp_files["valid_pathogens"])
    assert isinstance(pathogens, list)
    assert len(pathogens) == 16
    assert 'P1' in pathogens


def test_split_pathogen_stratified(sample_interactions, sample_valid_pathogens):
    """Test pathogen-stratified splitting."""
    train_df, val_df, holdout_df = split_pathogen_stratified(
        sample_interactions, 
        sample_valid_pathogens,
        test_size=0.2,
        val_size=0.1,
        holdout_size=3,
        random_state=42
    )
    
    # Check that splits are disjoint
    train_pathogens = set(train_df['pathogen_id'].unique())
    val_pathogens = set(val_df['pathogen_id'].unique())
    holdout_pathogens = set(holdout_df['pathogen_id'].unique())
    
    assert train_pathogens.isdisjoint(val_pathogens)
    assert train_pathogens.isdisjoint(holdout_pathogens)
    assert val_pathogens.isdisjoint(holdout_pathogens)
    
    # Check that all pathogens are assigned
    all_pathogens = train_pathogens | val_pathogens | holdout_pathogens
    assert all_pathogens.issubset(set(sample_valid_pathogens))


def test_save_split_metadata(sample_interactions, sample_valid_pathogens):
    """Test saving split metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        train_df, val_df, holdout_df = split_pathogen_stratified(
            sample_interactions, 
            sample_valid_pathogens,
            holdout_size=3,
            random_state=42
        )
        
        metadata = save_split_metadata(train_df, val_df, holdout_df, tmpdir)
        
        assert 'train' in metadata
        assert 'val' in metadata
        assert 'holdout' in metadata
        assert metadata['train']['num_rows'] == len(train_df)
        
        # Check file was created
        metadata_path = Path(tmpdir) / "split_metadata.json"
        assert metadata_path.exists()


def test_run_preprocessing_pipeline(temp_files):
    """Test full preprocessing pipeline."""
    result = run_preprocessing_pipeline(
        interaction_file=temp_files["interactions"],
        valid_pathogens_file=temp_files["valid_pathogens"],
        output_dir=temp_files["output_dir"],
        random_state=42
    )
    
    assert 'train_file' in result
    assert 'val_file' in result
    assert 'holdout_file' in result
    assert 'metadata' in result
    assert 'quality_report' in result
    
    # Check files exist
    assert os.path.exists(result['train_file'])
    assert os.path.exists(result['val_file'])
    assert os.path.exists(result['holdout_file'])
    assert os.path.exists(result['quality_report'])


def test_split_with_insufficient_pathogens(sample_interactions):
    """Test that splitting fails with insufficient pathogens."""
    small_pathogens = ['P1', 'P2', 'P3']  # Only 3 pathogens
    
    with pytest.raises(ValueError, match="Insufficient pathogens"):
        split_pathogen_stratified(
            sample_interactions,
            small_pathogens,
            holdout_size=5  # Need more than available
        )