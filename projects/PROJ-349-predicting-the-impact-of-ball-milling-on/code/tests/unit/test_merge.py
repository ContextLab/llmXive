import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from src.ingest.merge import merge_datasets, run_merge_pipeline, calculate_row_hash
from src.exceptions import DataIngestionError

@pytest.fixture
def sample_df_1():
    return pd.DataFrame({
        "material_type": ["Al", "Cu"],
        "milling_speed": [300, 400],
        "milling_time": [10, 20],
        "ball_to_powder_ratio": [2.0, 3.0],
        "youngs_modulus": [70, 110],
        "density": [2.7, 8.9],
        "d10": [1.0, 2.0],
        "d50": [5.0, 10.0],
        "d90": [10.0, 20.0],
        "source": ["mp", "nist"]
    })

@pytest.fixture
def sample_df_2():
    # Duplicate of first row in df1, different source
    return pd.DataFrame({
        "material_type": ["Al", "Ti"],
        "milling_speed": [300, 500],
        "milling_time": [10, 30],
        "ball_to_powder_ratio": [2.0, 4.0],
        "youngs_modulus": [70, 115],
        "density": [2.7, 4.5],
        "d10": [1.1, 3.0],  # Slightly different d10 for Al
        "d50": [5.1, 15.0],
        "d90": [10.1, 30.0],
        "source": ["arxiv", "nist"]
    })

@pytest.fixture
def empty_df():
    return pd.DataFrame(columns=["material_type", "d50"])

def test_merge_no_duplicates(sample_df_1, sample_df_2):
    """Test merging when there are no duplicates."""
    # Modify df2 to remove the duplicate row
    df2_no_dup = sample_df_2.iloc[1:].reset_index(drop=True)
    
    result = merge_datasets([sample_df_1, df2_no_dup])
    
    assert len(result) == 3  # 2 from df1 + 1 from df2
    assert "source" in result.columns

def test_merge_with_duplicates(sample_df_1, sample_df_2):
    """Test merging with duplicates (first row of df1 and df2 are same keys)."""
    result = merge_datasets([sample_df_1, sample_df_2])
    
    # Should be 3 rows: 1 merged (Al), 1 Cu, 1 Ti
    assert len(result) == 3
    
    # Check that the merged row has averaged values for d10, d50, d90
    al_row = result[result["material_type"] == "Al"].iloc[0]
    assert abs(al_row["d10"] - 1.05) < 0.01  # (1.0 + 1.1) / 2
    assert abs(al_row["d50"] - 5.05) < 0.01  # (5.0 + 5.1) / 2

def test_merge_empty_dataframe_list():
    """Test that empty list raises error."""
    with pytest.raises(DataIngestionError):
        merge_datasets([])

def test_merge_all_empty_dfs(empty_df):
    """Test that all empty dataframes raises error."""
    with pytest.raises(DataIngestionError):
        merge_datasets([empty_df, empty_df])

def test_merge_missing_columns(sample_df_1):
    """Test that missing required columns raises error."""
    bad_df = pd.DataFrame({"material_type": ["Al"], "d50": [5.0]})
    with pytest.raises(DataIngestionError):
        merge_datasets([sample_df_1, bad_df])

def test_calculate_row_hash(sample_df_1):
    """Test hash calculation."""
    hashes = calculate_row_hash(sample_df_1, ["material_type", "milling_speed"])
    assert len(hashes) == 2
    assert hashes.iloc[0] != hashes.iloc[1]

def test_run_merge_pipeline(tmp_path):
    """Test the full pipeline function with file I/O."""
    df1 = pd.DataFrame({
        "material_type": ["Al"],
        "milling_speed": [300],
        "milling_time": [10],
        "ball_to_powder_ratio": [2.0],
        "youngs_modulus": [70],
        "density": [2.7],
        "d10": [1.0],
        "d50": [5.0],
        "d90": [10.0],
        "source": ["mp"]
    })
    
    input_file = tmp_path / "input1.parquet"
    output_file = tmp_path / "output.parquet"
    
    df1.to_parquet(input_file)
    
    result = run_merge_pipeline([input_file], output_file, source_labels=["mp"])
    
    assert result is not None
    assert len(result) == 1
    assert output_file.exists()
    
    # Verify output content
    loaded = pd.read_parquet(output_file)
    assert len(loaded) == 1
    assert loaded.iloc[0]["source"] == "mp"