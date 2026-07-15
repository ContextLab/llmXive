"""
Unit tests for the storage module.
Verifies that data can be saved and loaded correctly with deterministic seeds.
"""
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

from models import SimulatedDataset, PowerMetric
from code.data.storage import (
    save_simulated_datasets,
    save_power_metrics,
    generate_run_id,
    _ensure_dir,
    save_simulation_manifest
)


class TestStorageUtils:
    """Tests for storage utility functions."""

    def test_ensure_dir_creates_directory(self, tmp_path):
        """Test that _ensure_dir creates a non-existent directory."""
        new_dir = tmp_path / "nested" / "path"
        assert not new_dir.exists()
        
        _ensure_dir(str(new_dir / "file.txt"))
        
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_generate_run_id_deterministic(self):
        """Test that run IDs are deterministic for the same inputs."""
        seed = 42
        snr = 1.5
        sparsity = 0.5
        dataset_id = 100

        id1 = generate_run_id(seed, snr, sparsity, dataset_id)
        id2 = generate_run_id(seed, snr, sparsity, dataset_id)

        assert id1 == id2
        assert isinstance(id1, str)
        assert len(id1) == 16

    def test_generate_run_id_unique(self):
        """Test that different inputs produce different run IDs."""
        id1 = generate_run_id(42, 1.0, 0.5, 100)
        id2 = generate_run_id(43, 1.0, 0.5, 100)
        id3 = generate_run_id(42, 2.0, 0.5, 100)

        assert id1 != id2
        assert id1 != id3
        assert id2 != id3


class TestSaveSimulatedDatasets:
    """Tests for saving SimulatedDataset objects."""

    def test_save_parquet(self, tmp_path):
        """Test saving datasets to Parquet format."""
        datasets = [
            SimulatedDataset(
                X=[[1.0, 2.0]],
                Y=[1.0],
                true_coefficients=[0.5],
                snr=1.0,
                sparsity=0.5,
                seed=42,
                dataset_id=123
            )
        ]
        
        output_path = str(tmp_path / "datasets.parquet")
        
        result_path = save_simulated_datasets(datasets, output_path, "parquet")
        
        assert os.path.exists(result_path)
        
        # Verify we can read it back
        df = pd.read_parquet(result_path)
        assert len(df) == 1
        assert "seed" in df.columns
        assert df.iloc[0]["seed"] == 42

    def test_save_csv(self, tmp_path):
        """Test saving datasets to CSV format."""
        datasets = [
            SimulatedDataset(
                X=[[1.0, 2.0], [3.0, 4.0]],
                Y=[1.0, 2.0],
                true_coefficients=[0.5, -0.5],
                snr=2.0,
                sparsity=0.3,
                seed=123,
                dataset_id=456
            )
        ]
        
        output_path = str(tmp_path / "datasets.csv")
        
        result_path = save_simulated_datasets(datasets, output_path, "csv")
        
        assert os.path.exists(result_path)
        
        # Verify we can read it back
        df = pd.read_csv(result_path)
        assert len(df) == 1
        assert df.iloc[0]["seed"] == 123

    def test_save_empty_list(self, tmp_path):
        """Test that saving an empty list returns empty string and logs warning."""
        output_path = str(tmp_path / "empty.parquet")
        result_path = save_simulated_datasets([], output_path)
        
        assert result_path == ""
        assert not os.path.exists(output_path)

    def test_invalid_format(self, tmp_path):
        """Test that invalid file format raises ValueError."""
        datasets = [
            SimulatedDataset(
                X=[[1.0]], Y=[1.0], true_coefficients=[0.5],
                snr=1.0, sparsity=0.5, seed=42, dataset_id=1
            )
        ]
        
        output_path = str(tmp_path / "datasets.xyz")
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            save_simulated_datasets(datasets, output_path, "xyz")


class TestSavePowerMetrics:
    """Tests for saving PowerMetric objects."""

    def test_save_metrics_csv(self, tmp_path):
        """Test saving power metrics to CSV."""
        metrics = [
            PowerMetric(
                method="ForwardStepwise",
                snr=1.0,
                sparsity=0.5,
                alpha=0.05,
                power_rate=0.85,
                ci_lower=0.75,
                ci_upper=0.95
            )
        ]
        
        output_path = str(tmp_path / "metrics.csv")
        
        result_path = save_power_metrics(metrics, output_path, "csv")
        
        assert os.path.exists(result_path)
        
        df = pd.read_csv(result_path)
        assert len(df) == 1
        assert df.iloc[0]["method"] == "ForwardStepwise"
        assert df.iloc[0]["power_rate"] == 0.85

    def test_save_metrics_parquet(self, tmp_path):
        """Test saving power metrics to Parquet."""
        metrics = [
            PowerMetric(
                method="LASSO",
                snr=2.0,
                sparsity=0.2,
                alpha=0.01,
                power_rate=0.92,
                ci_lower=0.88,
                ci_upper=0.96
            )
        ]
        
        output_path = str(tmp_path / "metrics.parquet")
        
        result_path = save_power_metrics(metrics, output_path, "parquet")
        
        assert os.path.exists(result_path)
        
        df = pd.read_parquet(result_path)
        assert len(df) == 1
        assert df.iloc[0]["method"] == "LASSO"


class TestSaveSimulationManifest:
    """Tests for saving simulation manifests."""

    def test_save_manifest(self, tmp_path):
        """Test saving a simulation manifest."""
        run_ids = ["abc123", "def456"]
        config = {"seed": 42, "snr_levels": [1.0, 2.0]}
        
        output_path = str(tmp_path / "manifest.json")
        
        result_path = save_simulation_manifest(run_ids, config, output_path)
        
        assert os.path.exists(result_path)
        
        import json
        with open(result_path, 'r') as f:
            manifest = json.load(f)
        
        assert manifest["total_runs"] == 2
        assert manifest["config"]["seed"] == 42
        assert "timestamp" in manifest