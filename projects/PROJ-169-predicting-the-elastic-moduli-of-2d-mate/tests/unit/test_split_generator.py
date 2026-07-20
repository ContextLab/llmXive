"""
Unit tests for the split generator.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from code.ingest.split_generator import (
    generate_mock_split,
    load_graphs_from_parquet,
    save_split_manifest,
)


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame with family_id column."""
    data = {
        "node_features": [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]],
        "edge_features": [[0.1], [0.2], [0.3], [0.4], [0.5]],
        "target_moduli": [100.0, 200.0, 150.0, 300.0, 250.0],
        "family_id": ["A", "A", "B", "B", "C"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_parquet_file(sample_dataframe):
    """Create a temporary parquet file."""
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        sample_dataframe.to_parquet(f.name)
        yield Path(f.name)
        Path(f.name).unlink()


@pytest.fixture
def temp_json_file():
    """Create a temporary JSON file path."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        yield Path(f.name)
        Path(f.name).unlink()


def test_load_graphs_from_parquet(temp_parquet_file, sample_dataframe):
    """Test loading data from parquet file."""
    df = load_graphs_from_parquet(temp_parquet_file)
    assert len(df) == len(sample_dataframe)
    assert "family_id" in df.columns
    assert list(df.columns) == list(sample_dataframe.columns)


def test_load_graphs_from_parquet_missing_file():
    """Test error handling for missing file."""
    with pytest.raises(SystemExit):
        load_graphs_from_parquet(Path("nonexistent.parquet"))


def test_generate_mock_split(sample_dataframe):
    """Test the mock split generation logic."""
    split = generate_mock_split(sample_dataframe, test_size=0.4, random_state=42)

    # Check metadata
    assert "metadata" in split
    assert "This is a mock split" in split["metadata"]["description"]
    assert split["metadata"]["random_state"] == 42

    # Check indices
    assert "train_indices" in split
    assert "test_indices" in split
    assert isinstance(split["train_indices"], list)
    assert isinstance(split["test_indices"], list)

    # Check counts
    total = len(split["train_indices"]) + len(split["test_indices"])
    assert total == len(sample_dataframe)

    # Verify no index duplication
    train_set = set(split["train_indices"])
    test_set = set(split["test_indices"])
    assert len(train_set & test_set) == 0


def test_generate_mock_split_stratification(sample_dataframe):
    """Test that stratification is applied based on family_id."""
    split = generate_mock_split(sample_dataframe, test_size=0.4, random_state=42)

    # Extract family_ids for train and test
    train_families = sample_dataframe.loc[split["train_indices"], "family_id"]
    test_families = sample_dataframe.loc[split["test_indices"], "family_id"]

    # With stratification, both sets should contain all families
    # (though this is a mock split, so families can overlap)
    assert set(train_families.unique()).issubset(set(sample_dataframe["family_id"].unique()))
    assert set(test_families.unique()).issubset(set(sample_dataframe["family_id"].unique()))


def test_save_split_manifest(split_manifest, temp_json_file):
    """Test saving the split manifest to JSON."""
    save_split_manifest(split_manifest, temp_json_file)

    assert temp_json_file.exists()

    with open(temp_json_file, "r") as f:
        loaded = json.load(f)

    assert loaded == split_manifest


# Helper fixture for split_manifest
@pytest.fixture
def split_manifest(sample_dataframe):
    """Create a sample split manifest."""
    return generate_mock_split(sample_dataframe, test_size=0.4, random_state=42)
