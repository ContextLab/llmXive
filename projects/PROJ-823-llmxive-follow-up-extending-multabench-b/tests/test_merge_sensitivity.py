"""
Tests for the sensitivity output merging logic (T019b).
"""
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import pytest
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.merge_sensitivity_outputs import merge_sensitivity_outputs

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_parquet_files(temp_data_dir):
    """Create sample parquet files for multiple seeds."""
    seeds = [42, 123, 456]
    run_id = "test_run"
    files = []

    for seed in seeds:
        filename = f"embeddings_seed_{seed}_{run_id}.parquet"
        filepath = temp_data_dir / filename
        
        # Create dummy data
        data = {
            "dataset_id": [f"dataset_{i}" for i in range(10)],
            "run_id": [run_id] * 10,
            "seed": [seed] * 10,
            "embedding": [np.random.rand(512).tolist() for _ in range(10)]
        }
        df = pd.DataFrame(data)
        df.to_parquet(filepath, index=False)
        files.append(filepath)
    
    return files, run_id, seeds

def test_merge_sensitivity_outputs(sample_parquet_files, temp_data_dir):
    """Test that merge_sensitivity_outputs correctly merges files."""
    files, run_id, seeds = sample_parquet_files
    
    output_path = merge_sensitivity_outputs(temp_data_dir, run_id, seeds)
    
    # Check output file exists
    expected_filename = f"embeddings_sensitivity_merged_{run_id}.parquet"
    expected_path = temp_data_dir / expected_filename
    
    assert output_path == expected_path
    assert output_path.exists()
    
    # Check content
    merged_df = pd.read_parquet(output_path)
    
    # Should have 3 * 10 = 30 rows
    assert len(merged_df) == 30
    
    # Check columns
    assert "seed" in merged_df.columns
    assert "dataset_id" in merged_df.columns
    assert "run_id" in merged_id in merged_df.columns
    
    # Check seeds are present
    assert set(merged_df["seed"].unique()) == set(seeds)
    
    # Check run_id consistency
    assert all(merged_df["run_id"] == run_id)

def test_missing_input_file(temp_data_dir):
    """Test that FileNotFoundError is raised if an input file is missing."""
    run_id = "test_run"
    seeds = [42, 123] # 123 file doesn't exist
    
    with pytest.raises(FileNotFoundError):
        merge_sensitivity_outputs(temp_data_dir, run_id, seeds)
    
def test_empty_dataframe_handling(temp_data_dir):
    """Test behavior with empty dataframes (if logic allows)."""
    seeds = [42]
    run_id = "test_run"
    
    # Create an empty file
    filename = f"embeddings_seed_{seeds[0]}_{run_id}.parquet"
    filepath = temp_data_dir / filename
    pd.DataFrame(columns=["dataset_id", "run_id", "seed", "embedding"]).to_parquet(filepath)
    
    # This might result in an empty merged file or an error depending on implementation.
    # Assuming it creates an empty file.
    output_path = merge_sensitivity_outputs(temp_data_dir, run_id, seeds)
    assert output_path.exists()
    merged_df = pd.read_parquet(output_path)
    assert len(merged_df) == 0