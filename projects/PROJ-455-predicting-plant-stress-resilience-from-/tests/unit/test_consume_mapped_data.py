"""
Unit tests for T026: consume_mapped_data_for_validation
"""
import os
import pytest
import pandas as pd
import numpy as np
from analysis.pathway import consume_mapped_data_for_validation, map_to_kegg, load_kegg_mapping

@pytest.fixture
def mock_mapped_data(tmp_path):
    """Create a temporary mapped_data.parquet file for testing."""
    data = {
        'metabolite_name': ['Proline', 'Glutathione', 'ABA', 'Unknown'],
        'kegg_id': ['C00186', 'C00051', 'C00773', None],
        'concentration': [10.5, 5.2, 2.1, 8.0],
        'sample_id': [1, 2, 3, 4]
    }
    df = pd.DataFrame(data)
    output_path = os.path.join(tmp_path, "mapped_data.parquet")
    df.to_parquet(output_path, index=False)
    return output_path

def test_consume_mapped_data_success(mock_mapped_data):
    """Test successful consumption of mapped data."""
    df = consume_mapped_data_for_validation(mock_mapped_data)
    assert isinstance(df, pd.DataFrame)
    assert 'kegg_id' in df.columns
    assert len(df) == 4
    assert df['kegg_id'].notna().sum() == 3  # One is None

def test_consume_mapped_data_missing_file(tmp_path):
    """Test that FileNotFoundError is raised when file is missing."""
    missing_path = os.path.join(tmp_path, "nonexistent.parquet")
    with pytest.raises(FileNotFoundError):
        consume_mapped_data_for_validation(missing_path)

def test_consume_mapped_data_missing_columns(tmp_path):
    """Test that ValueError is raised when required columns are missing."""
    data = {
        'metabolite_name': ['Proline'],
        'concentration': [10.5]
    }
    df = pd.DataFrame(data)
    output_path = os.path.join(tmp_path, "bad_mapped_data.parquet")
    df.to_parquet(output_path, index=False)
    
    with pytest.raises(ValueError, match="Mapped data missing required columns"):
        consume_mapped_data_for_validation(output_path)

def test_map_to_kegg_creates_parquet(tmp_path):
    """Test that map_to_kegg creates the parquet file."""
    # Setup mock data
    raw_data = {
        'metabolite_name': ['Proline', 'Glutathione'],
        'concentration': [10.5, 5.2]
    }
    raw_df = pd.DataFrame(raw_data)
    
    # Create a mock mapping file
    mapping_data = {
        'metabolite_name': ['Proline', 'Glutathione'],
        'kegg_id': ['C00186', 'C00051']
    }
    mapping_df = pd.DataFrame(mapping_data)
    mapping_path = os.path.join(tmp_path, "kegg_mapping.tsv")
    mapping_df.to_csv(mapping_path, sep='\t', index=False)
    
    # Temporarily override the load_kegg_mapping path for this test
    import analysis.pathway as pathway_module
    original_load = pathway_module.load_kegg_mapping
    
    def mock_load():
        return mapping_df
    
    pathway_module.load_kegg_mapping = mock_load
    
    try:
        # Change working directory to tmp_path to simulate relative paths
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        # Create data/raw and data/processed dirs
        os.makedirs("data/raw", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        
        # Move mapping file to expected location
        os.rename(mapping_path, "data/raw/kegg_mapping.tsv")
        
        result_df = map_to_kegg(raw_df)
        
        # Verify file was created
        output_path = os.path.join("data/processed", "mapped_data.parquet")
        assert os.path.exists(output_path)
        
        # Verify content
        loaded_df = pd.read_parquet(output_path)
        assert 'kegg_id' in loaded_df.columns
        assert len(loaded_df) == 2
    finally:
        pathway_module.load_kegg_mapping = original_load
        os.chdir(old_cwd)