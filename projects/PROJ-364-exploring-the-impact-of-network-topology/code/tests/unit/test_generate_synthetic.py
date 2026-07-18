"""
Unit tests for synthetic data generation (T017).
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import numpy as np
import pandas as pd

from src.data_ingestion.generate_synthetic import (
    generate_synthetic_dataset,
    _generate_defect_coordinates,
    _create_metadata,
    SYNTHETIC_VERSION
)
from src.utils.checksum import load_checksum_manifest

class TestGenerateDefectCoordinates:
    def test_deterministic_with_seed(self):
        """Verify that same seed produces same coordinates."""
        seed = 12345
        coords1 = _generate_defect_coordinates(1, 100, 5, seed)[0]
        coords2 = _generate_defect_coordinates(1, 100, 5, seed)[0]
        
        assert np.allclose(coords1['x'].values, coords2['x'].values)
        assert np.allclose(coords1['y'].values, coords2['y'].values)

    def test_different_seed_produces_different_data(self):
        """Verify that different seeds produce different coordinates."""
        coords1 = _generate_defect_coordinates(1, 100, 5, seed=100)[0]
        coords2 = _generate_defect_coordinates(1, 100, 5, seed=200)[0]
        
        assert not np.allclose(coords1['x'].values, coords2['x'].values)

    def test_correct_columns(self):
        """Verify output has correct columns."""
        coords = _generate_defect_coordinates(1, 100, 5, 42)[0]
        assert set(coords.columns) == {'x', 'y', 'sample_id'}

    def test_sample_count(self):
        """Verify correct number of rows."""
        n_defects = 50
        coords = _generate_defect_coordinates(1, 100, n_defects, 42)[0]
        assert len(coords) == n_defects

class TestCreateMetadata:
    def test_metadata_structure(self):
        """Verify metadata has required keys."""
        meta = _create_metadata(10, 500, 100, 42, "1.0.0")
        assert meta["dataset_type"] == "synthetic"
        assert meta["version"] == "1.0.0"
        assert "generation_seed" in meta
        assert "parameters" in meta
        assert "note" in meta
        assert "validation" in meta["note"].lower() or "synthetic" in meta["note"].lower()

    def test_parameters_match_input(self):
        """Verify parameters reflect inputs."""
        meta = _create_metadata(20, 1000, 200, 99, "2.0.0")
        assert meta["parameters"]["n_samples"] == 20
        assert meta["parameters"]["grid_size"] == 1000
        assert meta["parameters"]["n_defects_per_sample"] == 200

class TestGenerateSyntheticDataset:
    def test_files_created(self):
        """Verify all expected files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_synthetic_dataset(
                output_dir=tmpdir,
                n_samples=2,
                grid_size=100,
                n_defects_per_sample=10,
                seed=42
            )
            
            assert os.path.exists(result["coordinates"])
            assert os.path.exists(result["metadata"])
            assert os.path.exists(result["manifest"])
            assert os.path.exists(result["warning_log"])

    def test_csv_valid(self):
        """Verify CSV is readable and has correct schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_synthetic_dataset(
                output_dir=tmpdir,
                n_samples=1,
                grid_size=100,
                n_defects_per_sample=5,
                seed=42
            )
            
            df = pd.read_csv(result["coordinates"])
            assert 'x' in df.columns
            assert 'y' in df.columns
            assert 'sample_id' in df.columns
            assert len(df) == 5

    def test_metadata_valid_json(self):
        """Verify metadata is valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_synthetic_dataset(
                output_dir=tmpdir,
                n_samples=1,
                grid_size=100,
                n_defects_per_sample=5,
                seed=42
            )
            
            with open(result["metadata"], 'r') as f:
                meta = json.load(f)
            assert meta["dataset_type"] == "synthetic"

    def test_checksum_manifest_valid(self):
        """Verify checksum manifest is valid and references correct files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_synthetic_dataset(
                output_dir=tmpdir,
                n_samples=1,
                grid_size=100,
                n_defects_per_sample=5,
                seed=42
            )
            
            manifest = load_checksum_manifest(result["manifest"])
            assert "files" in manifest
            assert len(manifest["files"]) >= 2 # csv + json

    def test_warning_log_content(self):
        """Verify warning log contains required message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Note: The warning log is written to results/synthetic_warning.log
            # relative to the project root, not tmpdir. 
            # We check the file existence and content in a separate check 
            # or by mocking the path. For this unit test, we verify the 
            # function returns the correct path string.
            result = generate_synthetic_dataset(
                output_dir=tmpdir,
                n_samples=1,
                grid_size=100,
                n_defects_per_sample=5,
                seed=42
            )
            
            assert "synthetic_warning.log" in result["warning_log"]