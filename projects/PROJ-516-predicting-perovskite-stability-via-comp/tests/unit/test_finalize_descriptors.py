"""
tests/unit/test_finalize_descriptors.py

Unit tests for finalize_descriptors.py (T017).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pandas as pd
import pytest

# Mock the state manager to avoid file system writes in tests
import sys
from unittest.mock import MagicMock, patch

# We need to import the module under test
# Since it imports from utils.state_manager, we need to mock that too
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from code.finalize_descriptors import (
    load_descriptors,
    load_uncertainty_flags,
    merge_uncertainty,
    ensure_perovskite_family,
    save_descriptors,
    update_state,
    main,
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_descriptors_df():
    data = {
        "formula": ["CsPbI3", "FASnI3", "MA2AgBiI6"],
        "T_d": [350.0, 320.0, 400.0],
        "atomic_fraction_A": [0.33, 0.33, 0.25],
        "weighted_ionic_radius": [1.8, 1.9, 2.0],
        "T_d_uncertainty": [5.0, 10.0, 15.0],
        "perovskite_family": ["lead-halide", "tin-halide", "double perovskite"],
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_uncertainty_flags():
    return {
        "CsPbI3": 5.0,
        "FASnI3": 10.0,
        "MA2AgBiI6": 15.0,
    }

def test_load_descriptors_success(sample_descriptors_df, temp_dir):
    # Create a mock CSV file
    csv_path = temp_dir / "descriptors.csv"
    sample_descriptors_df.to_csv(csv_path, index=False)

    # Mock the global path in the module
    with mock.patch("code.finalize_descriptors.DESCRIPTORS_CSV", csv_path):
        df = load_descriptors()
        assert len(df) == 3
        assert "formula" in df.columns

def test_load_descriptors_missing_file(temp_dir):
    csv_path = temp_dir / "missing.csv"
    with mock.patch("code.finalize_descriptors.DESCRIPTORS_CSV", csv_path):
        with pytest.raises(FileNotFoundError):
            load_descriptors()

def test_load_uncertainty_flags_success(sample_uncertainty_flags, temp_dir):
    json_path = temp_dir / "uncertainty_flags.json"
    with open(json_path, 'w') as f:
        json.dump(sample_uncertainty_flags, f)

    with mock.patch("code.finalize_descriptors.UNCERTAINTY_FLAGS_FILE", json_path):
        data = load_uncertainty_flags()
        assert data == sample_uncertainty_flags

def test_load_uncertainty_flags_missing_file(temp_dir):
    json_path = temp_dir / "missing.json"
    with mock.patch("code.finalize_descriptors.UNCERTAINTY_FLAGS_FILE", json_path):
        data = load_uncertainty_flags()
        assert data == {}

def test_merge_uncertainty_adds_column(sample_descriptors_df, sample_uncertainty_flags, temp_dir):
    # Remove the column to test merging
    df = sample_descriptors_df.drop(columns=["T_d_uncertainty"])
    
    # Mock paths
    csv_path = temp_dir / "test.csv"
    json_path = temp_dir / "flags.json"
    
    df.to_csv(csv_path, index=False)
    with open(json_path, 'w') as f:
        json.dump(sample_uncertainty_flags, f)

    with mock.patch("code.finalize_descriptors.DESCRIPTORS_CSV", csv_path):
        with mock.patch("code.finalize_descriptors.UNCERTAINTY_FLAGS_FILE", json_path):
            # Re-load to get fresh df
            df_loaded = pd.read_csv(csv_path)
            df_merged = merge_uncertainty(df_loaded, sample_uncertainty_flags)
            
            assert "T_d_uncertainty" in df_merged.columns
            assert df_merged.loc[0, "T_d_uncertainty"] == 5.0

def test_ensure_perovskite_family_missing_column(sample_descriptors_df, temp_dir):
    df = sample_descriptors_df.drop(columns=["perovskite_family"])
    csv_path = temp_dir / "test.csv"
    df.to_csv(csv_path, index=False)

    with mock.patch("code.finalize_descriptors.DESCRIPTORS_CSV", csv_path):
        with pytest.raises(ValueError, match="perovskite_family column missing"):
            # We need to load the df again to simulate the state
            df_fresh = pd.read_csv(csv_path)
            ensure_perovskite_family(df_fresh)

def test_save_descriptors(sample_descriptors_df, temp_dir):
    output_path = temp_dir / "output.csv"
    save_descriptors(sample_descriptors_df, output_path)
    
    assert output_path.exists()
    df_out = pd.read_csv(output_path)
    assert len(df_out) == 3

def test_update_state(temp_dir):
    # Create a dummy file
    file_path = temp_dir / "dummy.csv"
    file_path.write_text("test")
    
    state_dir = temp_dir / "state"
    state_dir.mkdir()

    with mock.patch("code.finalize_descriptors.PROJECT_ROOT", temp_dir):
        with mock.patch("code.finalize_descriptors.STATE_DIR", state_dir):
            # Mock compute_sha256 and update_artifact_state
            with patch("code.finalize_descriptors.compute_sha256", return_value="abc123"):
                with patch("code.finalize_descriptors.update_artifact_state") as mock_update:
                    update_state(file_path)
                    mock_update.assert_called_once()

def test_main_success(sample_descriptors_df, sample_uncertainty_flags, temp_dir):
    # Setup files
    csv_path = temp_dir / "descriptors.csv"
    json_path = temp_dir / "uncertainty_flags.json"
    state_dir = temp_dir / "state"
    state_dir.mkdir()
    processed_dir = temp_dir / "data" / "processed"
    processed_dir.mkdir(parents=True)
    raw_dir = temp_dir / "data" / "raw"
    raw_dir.mkdir(parents=True)

    # Write initial data
    sample_descriptors_df.to_csv(csv_path, index=False)
    with open(json_path, 'w') as f:
        json.dump(sample_uncertainty_flags, f)

    # Mock paths
    with mock.patch("code.finalize_descriptors.PROJECT_ROOT", temp_dir):
        with mock.patch("code.finalize_descriptors.DESCRIPTORS_CSV", csv_path):
            with mock.patch("code.finalize_descriptors.UNCERTAINTY_FLAGS_FILE", json_path):
                with mock.patch("code.finalize_descriptors.STATE_DIR", state_dir):
                    with patch("code.finalize_descriptors.compute_sha256", return_value="hash123"):
                        with patch("code.finalize_descriptors.update_artifact_state") as mock_update:
                            result = main()
                            assert result == 0
                            mock_update.assert_called_once()

def test_main_missing_columns(sample_descriptors_df, temp_dir):
    # Create df without required columns
    df_missing = sample_descriptors_df.drop(columns=["T_d_uncertainty", "perovskite_family"])
    csv_path = temp_dir / "descriptors.csv"
    df_missing.to_csv(csv_path, index=False)
    
    state_dir = temp_dir / "state"
    state_dir.mkdir()

    with mock.patch("code.finalize_descriptors.PROJECT_ROOT", temp_dir):
        with mock.patch("code.finalize_descriptors.DESCRIPTORS_CSV", csv_path):
            with mock.patch("code.finalize_descriptors.UNCERTAINTY_FLAGS_FILE", temp_dir / "missing.json"):
                with mock.patch("code.finalize_descriptors.STATE_DIR", state_dir):
                    result = main()
                    assert result == 1
