"""
Tests for the traceability map generator (T006).

These tests verify that the traceability map correctly links output metrics
to source data rows and handles edge cases.
"""

import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Import from project API surface
from code.utils.traceability import (
    load_processed_data,
    load_source_metadata,
    map_metrics_to_sources,
    generate_traceability_map
)
from code.exceptions import MissingDataError, ConfigurationError


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_processed_csv(temp_dir):
    """Create a sample processed CSV file."""
    data = {
        "precinct_sum": [100, 200, 300],
        "county_reported": [102, 198, 305],
        "discrepancy_abs": [2, -2, 5],
        "discrepancy_pct": [0.02, -0.01, 0.016],
        "missing_data": [False, False, True],
        "source_row_id": ["row_001", "row_002", "row_003"],
        "source_file": ["election_data.csv"] * 3
    }
    df = pd.DataFrame(data)
    path = Path(temp_dir) / "processed.csv"
    df.to_csv(path, index=False)
    return str(path)


@pytest.fixture
def sample_source_csv(temp_dir):
    """Create a sample source CSV file."""
    data = {
        "id": ["row_001", "row_002", "row_003"],
        "precinct_votes": [100, 200, 300],
        "county_total": [102, 198, 305]
    }
    df = pd.DataFrame(data)
    path = Path(temp_dir) / "election_data.csv"
    df.to_csv(path, index=False)
    return str(path)


def test_load_processed_data_valid(sample_processed_csv):
    """Test loading a valid processed CSV."""
    df = load_processed_data(sample_processed_csv)
    assert len(df) == 3
    assert "precinct_sum" in df.columns
    assert "discrepancy_abs" in df.columns


def test_load_processed_data_missing_file(temp_dir):
    """Test loading a missing processed CSV raises MissingDataError."""
    with pytest.raises(MissingDataError):
        load_processed_data(str(Path(temp_dir) / "nonexistent.csv"))


def test_load_source_metadata(sample_source_csv):
    """Test loading source metadata."""
    meta = load_source_metadata(sample_source_csv)
    assert "sha256" in meta
    assert "size_bytes" in meta
    assert meta["filename"] == "election_data.csv"
    assert meta["checksum_valid"] is True


def test_map_metrics_to_sources(sample_processed_csv):
    """Test mapping metrics to sources."""
    df = load_processed_data(sample_processed_csv)
    mapping = map_metrics_to_sources(df)

    assert len(mapping) == 3
    assert mapping[0]["output_index"] == 0
    assert mapping[0]["source_reference"]["row_id"] == "row_001"
    assert mapping[0]["discrepancy_abs"] == 2


def test_generate_traceability_map_full_flow(temp_dir, sample_processed_csv, sample_source_csv):
    """Test the full generation of a traceability map."""
    output_path = Path(temp_dir) / "traceability_map.json"

    result_path = generate_traceability_map(
        processed_data_path=sample_processed_csv,
        source_data_path=sample_source_csv,
        output_path=str(output_path)
    )

    assert Path(result_path).exists()

    with open(result_path, 'r') as f:
        data = json.load(f)

    assert data["version"] == "1.0"
    assert "source_data" in data
    assert "row_mappings" in data
    assert len(data["row_mappings"]) == 3
    assert data["processed_data"]["row_count"] == 3


def test_generate_traceability_map_empty_processed(temp_dir, sample_source_csv):
    """Test generation with an empty processed file."""
    empty_df = pd.DataFrame(columns=["precinct_sum", "county_reported"])
    empty_path = Path(temp_dir) / "empty.csv"
    empty_df.to_csv(empty_path, index=False)

    with pytest.raises(MissingDataError):
        generate_traceability_map(
            processed_data_path=str(empty_path),
            source_data_path=sample_source_csv,
            output_path=str(Path(temp_dir) / "out.json")
        )