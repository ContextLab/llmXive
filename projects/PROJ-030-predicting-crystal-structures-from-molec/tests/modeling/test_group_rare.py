"""
Tests for code/modeling/group_rare.py (Task T015a).
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from modeling.group_rare import (
    load_dataset,
    group_rare_space_groups,
    save_dataset,
    run_grouping,
    RARE_THRESHOLD,
    RARE_LABEL,
    SPACE_GROUP_COLUMN
)


@pytest.fixture
def sample_dataset(tmp_path):
    """Create a sample dataset with known space group distribution."""
    data = {
        "id": range(100),
        "smiles": ["CCO" for _ in range(100)],
        "space_group": (
            ["P1" for _ in range(50)] +  # Common group
            ["P2_1" for _ in range(30)] +  # Common group
            ["P2_1/c" for _ in range(15)] +  # Rare group (< 20)
            ["C2/c" for _ in range(5)]  # Rare group (< 20)
        ),
        "lattice_a": [1.0] * 100,
        "lattice_b": [1.0] * 100,
        "lattice_c": [1.0] * 100,
        "fingerprint_bits": ["0" * 2048] * 100
    }
    df = pd.DataFrame(data)
    output_path = tmp_path / "crystal_dataset.csv"
    df.to_csv(output_path, index=False)
    return output_path, df


def test_load_dataset(sample_dataset):
    """Test loading a dataset from CSV."""
    input_path, _ = sample_dataset
    df = load_dataset(input_path)
    assert len(df) == 100
    assert SPACE_GROUP_COLUMN in df.columns


def test_group_rare_space_groups(sample_dataset):
    """Test grouping rare space groups."""
    _, df = sample_dataset
    
    # Before grouping
    value_counts_before = df[SPACE_GROUP_COLUMN].value_counts()
    assert value_counts_before["P1"] == 50
    assert value_counts_before["P2_1/c"] == 15
    assert value_counts_before["C2/c"] == 5
    
    # Group rare space groups
    df_grouped = group_rare_space_groups(df, threshold=RARE_THRESHOLD)
    
    # After grouping
    value_counts_after = df_grouped[SPACE_GROUP_COLUMN].value_counts()
    
    # Common groups should remain unchanged
    assert value_counts_after["P1"] == 50
    assert value_counts_after["P2_1"] == 30
    
    # Rare groups should be combined into 'Other'
    assert RARE_LABEL in value_counts_after
    assert value_counts_after[RARE_LABEL] == 20  # 15 + 5
    
    # Rare groups should no longer exist as distinct values
    assert "P2_1/c" not in value_counts_after
    assert "C2/c" not in value_counts_after


def test_no_rare_groups(tmp_path):
    """Test behavior when no space groups are rare."""
    data = {
        "id": range(100),
        "smiles": ["CCO" for _ in range(100)],
        "space_group": ["P1" for _ in range(100)],
        "lattice_a": [1.0] * 100,
        "lattice_b": [1.0] * 100,
        "lattice_c": [1.0] * 100,
        "fingerprint_bits": ["0" * 2048] * 100
    }
    df = pd.DataFrame(data)
    input_path = tmp_path / "crystal_dataset.csv"
    df.to_csv(input_path, index=False)
    
    loaded_df = load_dataset(input_path)
    df_grouped = group_rare_space_groups(loaded_df, threshold=RARE_THRESHOLD)
    
    # No changes should be made
    assert df_grouped[SPACE_GROUP_COLUMN].value_counts()["P1"] == 100
    assert RARE_LABEL not in df_grouped[SPACE_GROUP_COLUMN].values


def test_save_dataset(sample_dataset, tmp_path):
    """Test saving a dataset to CSV."""
    _, df = sample_dataset
    df_grouped = group_rare_space_groups(df)
    
    output_path = tmp_path / "grouped_dataset.csv"
    save_dataset(df_grouped, output_path)
    
    assert output_path.exists()
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == len(df_grouped)
    assert RARE_LABEL in saved_df[SPACE_GROUP_COLUMN].values


def test_run_grouping_full_flow(sample_dataset, tmp_path):
    """Test the full run_grouping function."""
    input_path, _ = sample_dataset
    output_path = tmp_path / "grouped_dataset.csv"
    
    result = run_grouping(input_path=input_path, output_path=output_path)
    
    assert result["status"] == "success"
    assert result["input_rows"] == 100
    assert result["output_rows"] == 100
    assert result["threshold_used"] == RARE_THRESHOLD
    assert result["rare_label"] == RARE_LABEL
    assert output_path.exists()
    
    # Verify the output file content
    saved_df = pd.read_csv(output_path)
    assert RARE_LABEL in saved_df[SPACE_GROUP_COLUMN].values
    assert "P2_1/c" not in saved_df[SPACE_GROUP_COLUMN].values
    assert "C2/c" not in saved_df[SPACE_GROUP_COLUMN].values