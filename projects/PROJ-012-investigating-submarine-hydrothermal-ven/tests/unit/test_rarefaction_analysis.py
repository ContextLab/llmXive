"""
Unit tests for T020b: Rarefaction Analysis and Depth Determination.

These tests verify the logic of curve generation and depth determination
without relying on large real datasets.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import yaml
import tempfile
import os

# Import the functions to test
# Note: We assume the code is in code/rarefaction_analysis.py
# We need to import from the code module.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from rarefaction_analysis import (
    generate_rarefaction_curves,
    determine_optimal_depth,
    run_rarefaction_depth_analysis
)

@pytest.fixture
def mock_otu_table():
    """Create a small, deterministic mock OTU table."""
    data = {
        'feat_A': [100, 500, 200, 50],
        'feat_B': [50, 200, 100, 20],
        'feat_C': [20, 100, 50, 5],
        'feat_D': [10, 50, 25, 2],
        'feat_E': [5, 25, 12, 1]
    }
    # Create a DataFrame with sample IDs as index
    df = pd.DataFrame(data, index=['sample_1', 'sample_2', 'sample_3', 'sample_4'])
    return df

@pytest.fixture
def mock_depths():
    return [50, 100, 150, 200]

def test_generate_rarefaction_curves(mock_otu_table, mock_depths):
    """Test that curve generation produces expected structure."""
    result = generate_rarefaction_curves(mock_otu_table, mock_depths, n_iterations=2)
    
    assert isinstance(result, pd.DataFrame)
    assert 'sample_id' in result.columns
    assert 'depth' in result.columns
    assert 'iteration' in result.columns
    assert 'shannon_diversity' in result.columns
    
    # Check that we have results for all depths that are valid
    # sample_4 has total 78, so depths 100+ should be skipped for it
    valid_depths_for_sample4 = [d for d in mock_depths if d <= 78]
    
    # Check sample_4 rows
    sample4_rows = result[result['sample_id'] == 'sample_4']
    assert len(sample4_rows['depth'].unique()) == len(valid_depths_for_sample4)

def test_determine_optimal_depth_plateau():
    """Test depth determination when a plateau is present."""
    # Construct data that plateaus
    # Depth 100 -> mean 2.0
    # Depth 200 -> mean 2.01 (very small slope)
    data = {
        'depth': [100, 100, 200, 200],
        'shannon_diversity': [2.0, 2.0, 2.01, 2.01]
    }
    df = pd.DataFrame(data)
    
    depth, rationale = determine_optimal_depth(df)
    
    assert depth is not None
    assert depth == 200 # The point where slope is small
    assert "plateaus" in rationale.lower()

def test_determine_optimal_depth_no_plateau():
    """Test depth determination when no plateau is found."""
    # Construct data that keeps increasing
    data = {
        'depth': [50, 100, 150, 200],
        'shannon_diversity': [1.0, 1.5, 2.0, 2.5]
    }
    df = pd.DataFrame(data)
    
    depth, rationale = determine_optimal_depth(df)
    
    # Should return max valid or None depending on implementation
    # Based on current logic, it returns max valid with a warning
    assert depth is not None
    assert depth == 200
    assert "No clear plateau" in rationale

def test_run_rarefaction_depth_analysis_integration(mock_otu_table, tmp_path):
    """Integration test for the full pipeline."""
    # Create a temporary OTU table
    otu_file = tmp_path / "otu_table.tsv"
    mock_otu_table.to_csv(otu_file, sep='\t')
    
    config_file = tmp_path / "rarefaction_config.yaml"
    
    # Run the analysis
    run_rarefaction_depth_analysis(
        otu_table_path=str(otu_file),
        output_config_path=str(config_file)
    )
    
    # Verify output exists
    assert config_file.exists()
    
    # Load and check content
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    assert 'optimal_rarefaction_depth' in config
    assert 'rationale' in config
    assert config['status'] in ['determined', 'deferred', 'failed']

def test_empty_otu_table(tmp_path):
    """Test handling of empty OTU table."""
    otu_file = tmp_path / "empty_otu.tsv"
    pd.DataFrame().to_csv(otu_file, sep='\t')
    
    config_file = tmp_path / "empty_config.yaml"
    
    run_rarefaction_depth_analysis(
        otu_table_path=str(otu_file),
        output_config_path=str(config_file)
    )
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    assert config['optimal_rarefaction_depth'] == '[deferred]'
    assert config['status'] == 'failed'
