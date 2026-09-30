import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from code.data.ingest import (
    download_data,
    align_maps,
    mask_defects,
    ingest_and_filter_dataset,
    load_feasibility_status,
)
from code.data.models import ElementalMap, DevicePerformance

class TestIngestModule:
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_root = tempfile.mkdtemp()
        raw_dir = Path(temp_root) / "raw"
        processed_dir = Path(temp_root) / "processed"
        state_dir = Path(temp_root) / "state"
        raw_dir.mkdir()
        processed_dir.mkdir()
        state_dir.mkdir()
        yield {
            "temp_root": Path(temp_root),
            "raw_dir": raw_dir,
            "processed_dir": processed_dir,
            "state_dir": state_dir,
        }
        shutil.rmtree(temp_root)
    
    def test_download_data_handles_empty_urls(self, temp_dirs):
        """Test that download_data handles empty URL lists gracefully."""
        result = download_data([], temp_dirs["raw_dir"])
        assert result == []
    
    def test_align_maps_requires_paths(self, temp_dirs):
        """Test that align_maps raises error with no paths."""
        with pytest.raises(ValueError, match="No map paths provided"):
            align_maps([])
    
    def test_mask_defects_returns_dict(self, temp_dirs):
        """Test that mask_defects returns a dictionary of masked arrays."""
        # Create simple test arrays
        test_maps = {
            "Pb": np.ones((10, 10)),
            "I": np.ones((10, 10)) * 2,
        }
        masked = mask_defects(test_maps, threshold=0.5)
        assert isinstance(masked, dict)
        assert "Pb" in masked
        assert "I" in masked
        assert masked["Pb"].shape == (10, 10)
    
    def test_ingest_and_filter_dataset_creates_output(self, temp_dirs):
        """Test that ingest_and_filter_dataset creates the output CSV."""
        # Create a minimal metadata CSV
        metadata_path = temp_dirs["raw_dir"] / "metadata.csv"
        metadata_data = {
            "sample_id": ["sample_001", "sample_002"],
            "PCE": [20.5, 21.3],
            "J_sc": [25.0, 26.1],
            "V_oc": [1.1, 1.15],
            "Pb_url": ["http://example.com/Pb.npy", "http://example.com/Pb2.npy"],
            "I_url": ["http://example.com/I.npy", "http://example.com/I2.npy"],
            "MA_url": ["http://example.com/MA.npy", "http://example.com/MA2.npy"],
        }
        pd.DataFrame(metadata_data).to_csv(metadata_path, index=False)
        
        # Create fake .npy files to simulate downloads
        for sample in ["sample_001", "sample_002"]:
            sample_dir = temp_dirs["raw_dir"] / sample
            sample_dir.mkdir()
            np.save(sample_dir / "Pb.npy", np.random.rand(10, 10))
            np.save(sample_dir / "I.npy", np.random.rand(10, 10))
            np.save(sample_dir / "MA.npy", np.random.rand(10, 10))
        
        output_path = temp_dirs["processed_dir"] / "unified_dataset.csv"
        
        # Run ingestion
        ingest_and_filter_dataset(
            metadata_csv=metadata_path,
            raw_dir=temp_dirs["raw_dir"],
            output_csv=output_path,
            performance_columns=["PCE", "J_sc", "V_oc"],
            state_dir=temp_dirs["state_dir"],
        )
        
        # Verify output
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert "sample_id" in df.columns
        assert "Pb_map_path" in df.columns
        assert "I_map_path" in df.columns
        assert "MA_map_path" in df.columns
        assert "PCE" in df.columns
        assert "J_sc" in df.columns
        assert "V_oc" in df.columns
    
    def test_ingest_filters_missing_performance_metrics(self, temp_dirs):
        """Test that samples missing performance metrics are excluded."""
        metadata_path = temp_dirs["raw_dir"] / "metadata.csv"
        metadata_data = {
            "sample_id": ["sample_001", "sample_002", "sample_003"],
            "PCE": [20.5, np.nan, 21.3],  # sample_002 missing PCE
            "J_sc": [25.0, 26.1, 26.5],
            "V_oc": [1.1, 1.15, 1.12],
            "Pb_url": ["http://example.com/Pb.npy"] * 3,
            "I_url": ["http://example.com/I.npy"] * 3,
            "MA_url": ["http://example.com/MA.npy"] * 3,
        }
        pd.DataFrame(metadata_data).to_csv(metadata_path, index=False)
        
        # Create fake .npy files
        for sample in ["sample_001", "sample_002", "sample_003"]:
            sample_dir = temp_dirs["raw_dir"] / sample
            sample_dir.mkdir()
            np.save(sample_dir / "Pb.npy", np.random.rand(10, 10))
            np.save(sample_dir / "I.npy", np.random.rand(10, 10))
            np.save(sample_dir / "MA.npy", np.random.rand(10, 10))
        
        output_path = temp_dirs["processed_dir"] / "unified_dataset.csv"
        
        ingest_and_filter_dataset(
            metadata_csv=metadata_path,
            raw_dir=temp_dirs["raw_dir"],
            output_csv=output_path,
            performance_columns=["PCE", "J_sc", "V_oc"],
            state_dir=temp_dirs["state_dir"],
        )
        
        df = pd.read_csv(output_path)
        # sample_002 should be excluded
        assert len(df) == 2
        assert "sample_002" not in df["sample_id"].values
    
    def test_load_feasibility_status_raises_on_missing(self, temp_dirs):
        """Test that load_feasibility_status raises FileNotFoundError when file missing."""
        with pytest.raises(FileNotFoundError):
            load_feasibility_status(temp_dirs["state_dir"])
    
    def test_ingest_handles_download_failures(self, temp_dirs):
        """Test that ingestion continues even if some downloads fail."""
        metadata_path = temp_dirs["raw_dir"] / "metadata.csv"
        metadata_data = {
            "sample_id": ["sample_001"],
            "PCE": [20.5],
            "J_sc": [25.0],
            "V_oc": [1.1],
            "Pb_url": ["http://invalid-url-9999.com/nonexistent.npy"],
            "I_url": ["http://invalid-url-9999.com/nonexistent.npy"],
            "MA_url": ["http://invalid-url-9999.com/nonexistent.npy"],
        }
        pd.DataFrame(metadata_data).to_csv(metadata_path, index=False)
        
        output_path = temp_dirs["processed_dir"] / "unified_dataset.csv"
        
        # Should not raise, but produce empty dataset or skip sample
        ingest_and_filter_dataset(
            metadata_csv=metadata_path,
            raw_dir=temp_dirs["raw_dir"],
            output_csv=output_path,
            performance_columns=["PCE", "J_sc", "V_oc"],
            state_dir=temp_dirs["state_dir"],
        )
        
        assert output_path.exists()
        df = pd.read_csv(output_path)
        # Sample should be skipped due to download failure
        assert len(df) == 0 or "sample_id" not in df.columns or len(df) == 0