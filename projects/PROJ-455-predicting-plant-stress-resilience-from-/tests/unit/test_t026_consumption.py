"""
Unit tests for T026: Consuming persisted KEGG mapping.
"""
import os
import pytest
import pandas as pd
import sys

# Ensure imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.pathway import (
    consume_mapped_data_for_validation,
    run_pathway_validation_script,
    map_to_kegg
)
from data.generator import generate_synthetic_data

@pytest.fixture
def mapped_data_path(tmp_path):
    """
    Creates a temporary mapped_data.parquet file for testing.
    """
    # Generate synthetic data
    df = generate_synthetic_data(n_samples=50, stress_type="drought", missing_rate=0.0, seed=42)
    
    # Mock mapping (since we can't rely on external KEGG file in unit test environment)
    # In a real integration test, we would use the real map_to_kegg
    df['kegg_id'] = [f"C0000{i}" for i in range(len(df))]
    
    output_dir = tmp_path / "data" / "processed"
    output_dir.mkdir(parents=True)
    output_path = output_dir / "mapped_data.parquet"
    
    df.to_parquet(output_path)
    return str(output_path)

def test_consume_mapped_data_exists(mapped_data_path):
    """
    Test that consume_mapped_data_for_validation successfully reads the parquet file.
    """
    df = consume_mapped_data_for_validation(mapped_data_path)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert 'kegg_id' in df.columns
    assert 'metabolite_name' in df.columns
    assert 'concentration' in df.columns

def test_consume_mapped_data_missing_file(tmp_path):
    """
    Test that consume_mapped_data_for_validation raises FileNotFoundError for missing file.
    """
    non_existent_path = str(tmp_path / "non_existent.parquet")
    
    with pytest.raises(FileNotFoundError) as exc_info:
        consume_mapped_data_for_validation(non_existent_path)
    
    assert "not found" in str(exc_info.value).lower()

def test_consume_mapped_data_missing_columns(tmp_path):
    """
    Test that consume_mapped_data_for_validation raises ValueError for missing columns.
    """
    # Create a parquet file with missing columns
    df = pd.DataFrame({
        'metabolite_name': ['A', 'B'],
        'concentration': [1.0, 2.0]
        # Missing 'kegg_id'
    })
    
    output_path = tmp_path / "bad_data.parquet"
    df.to_parquet(output_path)
    
    with pytest.raises(ValueError) as exc_info:
        consume_mapped_data_for_validation(str(output_path))
    
    assert "missing required columns" in str(exc_info.value).lower()

def test_run_pathway_validation_script(mapped_data_path):
    """
    Test that run_pathway_validation_script executes successfully and returns a result dict.
    """
    result = run_pathway_validation_script(mapped_data_path)
    
    assert isinstance(result, dict)
    assert 'input_file' in result
    assert 'unique_kegg_ids' in result
    assert 'jaccard_similarity' in result
    assert 'p_value' in result
    assert 'biological_alignment_valid' in result
    
    assert result['unique_kegg_ids'] > 0
    assert 0.0 <= result['jaccard_similarity'] <= 1.0
    assert 0.0 <= result['p_value'] <= 1.0
    assert isinstance(result['biological_alignment_valid'], bool)
