import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from src.data.preprocess import (
    load_interactions, 
    generate_sensitivity_dataset, 
    run_preprocessing_pipeline
)

@pytest.fixture
def sample_interactions():
    """Create a sample interaction dataframe with some missing combinations."""
    data = {
        'pathogen_id': ['P1', 'P1', 'P2', 'P2', 'P3'],
        'host_id': ['H1', 'H2', 'H1', 'H3', 'H1'],
        'label': [1, 0, 1, 1, -1]  # P3-H1 is unknown
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_generate_sensitivity_dataset_basic(sample_interactions, temp_output_dir):
    """Test that generate_sensitivity_dataset creates a dense matrix."""
    output_path = os.path.join(temp_output_dir, "sensitivity_interactions.csv")
    
    result = generate_sensitivity_dataset(sample_interactions, output_path)
    
    # Should have 3 pathogens x 3 hosts = 9 rows
    assert len(result) == 9
    
    # All labels should be 0 or 1 (no -1, no NaN)
    assert result['label'].isin([0, 1]).all()
    assert not result['label'].isna().any()
    
    # Check that original known interactions are preserved
    # P1-H1 should be 1, P1-H2 should be 0
    p1_h1 = result[(result['pathogen_id'] == 'P1') & (result['host_id'] == 'H1')]
    assert len(p1_h1) == 1
    assert p1_h1['label'].iloc[0] == 1
    
    p1_h2 = result[(result['pathogen_id'] == 'P1') & (result['host_id'] == 'H2')]
    assert len(p1_h2) == 1
    assert p1_h2['label'].iloc[0] == 0

def test_generate_sensitivity_dataset_imputes_missing(sample_interactions, temp_output_dir):
    """Test that missing combinations are imputed as 0."""
    output_path = os.path.join(temp_output_dir, "sensitivity_interactions.csv")
    
    result = generate_sensitivity_dataset(sample_interactions, output_path)
    
    # P2-H2 was missing in original, should be 0
    p2_h2 = result[(result['pathogen_id'] == 'P2') & (result['host_id'] == 'H2')]
    assert len(p2_h2) == 1
    assert p2_h2['label'].iloc[0] == 0
    
    # P3-H3 was missing, should be 0
    p3_h3 = result[(result['pathogen_id'] == 'P3') & (result['host_id'] == 'H3')]
    assert len(p3_h3) == 1
    assert p3_h3['label'].iloc[0] == 0

def test_generate_sensitivity_dataset_treats_unknown_as_negative(sample_interactions, temp_output_dir):
    """Test that -1 (unknown) labels are treated as 0."""
    output_path = os.path.join(temp_output_dir, "sensitivity_interactions.csv")
    
    result = generate_sensitivity_dataset(sample_interactions, output_path)
    
    # P3-H1 was -1 in original, should be 0 in sensitivity dataset
    p3_h1 = result[(result['pathogen_id'] == 'P3') & (result['host_id'] == 'H1')]
    assert len(p3_h1) == 1
    assert p3_h1['label'].iloc[0] == 0

def test_generate_sensitivity_dataset_saves_file(sample_interactions, temp_output_dir):
    """Test that the output file is actually written to disk."""
    output_path = os.path.join(temp_output_dir, "sensitivity_interactions.csv")
    
    result = generate_sensitivity_dataset(sample_interactions, output_path)
    
    assert os.path.exists(output_path)
    
    # Verify we can read it back
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == len(result)
    assert list(saved_df.columns) == ['pathogen_id', 'host_id', 'label']

def test_run_preprocessing_pipeline_generates_sensitivity(temp_interactions=None):
    """Integration test for the full pipeline generating sensitivity dataset."""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = os.path.join(tmpdir, "data")
        raw_dir = os.path.join(data_dir, "raw")
        processed_dir = os.path.join(data_dir, "processed")
        os.makedirs(raw_dir)
        os.makedirs(processed_dir)
        
        # Create sample interactions
        interactions = pd.DataFrame({
            'pathogen_id': ['P1', 'P1', 'P2'],
            'host_id': ['H1', 'H2', 'H1'],
            'label': [1, 0, 1]
        })
        interactions.to_csv(os.path.join(raw_dir, "interactions_merged.csv"), index=False)
        
        # Create valid pathogens list
        valid_pathogens = ['P1', 'P2']
        with open(os.path.join(processed_dir, "valid_pathogens.json"), 'w') as f:
            json.dump(valid_pathogens, f)
        
        # Run pipeline
        results = run_preprocessing_pipeline(data_dir, data_dir, seed=42)
        
        # Verify sensitivity dataset was generated
        assert "sensitivity_df" in results
        assert "sensitivity_path" in results
        assert os.path.exists(results["sensitivity_path"])
        
        # Verify it has the expected structure
        sens_df = results["sensitivity_df"]
        assert 'pathogen_id' in sens_df.columns
        assert 'host_id' in sens_df.columns
        assert 'label' in sens_df.columns
        assert len(sens_df) == 6  # 2 pathogens * 3 hosts (H1, H2 from data, plus H3? No, only H1, H2)
        # Actually: P1, P2 x H1, H2 = 4 rows
        assert len(sens_df) == 4

def test_generate_sensitivity_dataset_empty_input(temp_output_dir):
    """Test behavior with empty dataframe."""
    empty_df = pd.DataFrame(columns=['pathogen_id', 'host_id', 'label'])
    output_path = os.path.join(temp_output_dir, "empty_sensitivity.csv")
    
    # Should handle empty input gracefully (result in empty output)
    result = generate_sensitivity_dataset(empty_df, output_path)
    
    assert len(result) == 0
    assert os.path.exists(output_path)