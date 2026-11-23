"""
Unit tests for handle_missing_coords.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

from data.handle_missing_coords import handle_missing_coordinates


def test_handle_missing_coords_missing_3d():
    """Test that molecules with missing 3D coordinates are excluded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.json"
        output_path = Path(tmpdir) / "excluded.csv"

        # Create test data with missing coordinates
        data = [
            {"molecule_id": "mol1", "coordinates": None, "atoms": ["C", "O"]},
            {"molecule_id": "mol2", "coordinates": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], "atoms": ["C", "O"]}
        ]
        with open(input_path, 'w') as f:
            json.dump(data, f)

        excluded_df = handle_missing_coordinates(input_path, output_path)

        assert len(excluded_df) == 1
        assert excluded_df.iloc[0]['molecule_id'] == 'mol1'
        assert excluded_df.iloc[0]['exclusion_reason'] == 'missing_3d'
        assert output_path.exists()


def test_handle_missing_coords_nan_coordinates():
    """Test that molecules with NaN coordinates are excluded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.json"
        output_path = Path(tmpdir) / "excluded.csv"

        # Create test data with NaN coordinates
        data = [
            {"molecule_id": "mol3", "coordinates": [[np.nan, 0.0, 0.0], [1.0, 0.0, 0.0]], "atoms": ["C", "O"]},
            {"molecule_id": "mol4", "coordinates": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], "atoms": ["C", "O"]}
        ]
        with open(input_path, 'w') as f:
            json.dump(data, f)

        excluded_df = handle_missing_coordinates(input_path, output_path)

        assert len(excluded_df) == 1
        assert excluded_df.iloc[0]['molecule_id'] == 'mol3'
        assert excluded_df.iloc[0]['exclusion_reason'] == 'missing_3d'


def test_handle_missing_coords_invalid_structure():
    """Test that molecules with invalid structure (missing atoms) are excluded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.json"
        output_path = Path(tmpdir) / "excluded.csv"

        # Create test data with missing atoms
        data = [
            {"molecule_id": "mol5", "coordinates": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], "atoms": []},
            {"molecule_id": "mol6", "coordinates": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], "atoms": ["C", "O"]}
        ]
        with open(input_path, 'w') as f:
            json.dump(data, f)

        excluded_df = handle_missing_coordinates(input_path, output_path)

        assert len(excluded_df) == 1
        assert excluded_df.iloc[0]['molecule_id'] == 'mol5'
        assert excluded_df.iloc[0]['exclusion_reason'] == 'invalid_structure'


def test_handle_missing_coords_no_exclusions():
    """Test that valid molecules produce an empty exclusion report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.json"
        output_path = Path(tmpdir) / "excluded.csv"

        # Create valid test data
        data = [
            {"molecule_id": "mol7", "coordinates": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], "atoms": ["C", "O"]},
            {"molecule_id": "mol8", "coordinates": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], "atoms": ["C", "O", "H"]}
        ]
        with open(input_path, 'w') as f:
            json.dump(data, f)

        excluded_df = handle_missing_coordinates(input_path, output_path)

        assert len(excluded_df) == 0
        assert output_path.exists()
        # Check that file has headers even if empty
        df_check = pd.read_csv(output_path)
        assert list(df_check.columns) == ['molecule_id', 'exclusion_reason', 'exclusion_timestamp']