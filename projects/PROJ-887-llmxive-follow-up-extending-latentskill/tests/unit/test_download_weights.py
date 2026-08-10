"""
Unit tests for download_weights.py
"""
import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion.download_weights import generate_proxy_weights, save_weights

class TestGenerateProxyWeights:
    def test_proxy_weights_generated(self):
        """Test that proxy weights are generated with correct dimensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "proxy_weights.npz"
            generate_proxy_weights(output_path, seed=42)
            
            assert output_path.exists()
            
            data = np.load(output_path)
            assert "A" in data.files
            assert "B" in data.files
            
            # Check dimensions
            assert data["A"].shape[0] == 1024  # rank
            assert data["A"].shape[1] == 1024  # rank
            assert data["B"].shape[0] == 1024  # rank
            assert data["B"].shape[1] == 4096  # in_features
            
            # Check deterministic
            data2 = np.load(output_path)
            assert np.array_equal(data["A"], data2["A"])
            assert np.array_equal(data["B"], data2["B"])

    def test_proxy_weights_non_zero(self):
        """Test that proxy weights are non-zero."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "proxy_weights.npz"
            generate_proxy_weights(output_path, seed=42)
            
            data = np.load(output_path)
            assert not np.all(data["A"] == 0)
            assert not np.all(data["B"] == 0)

    def test_proxy_weights_no_nan(self):
        """Test that proxy weights have no NaN values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "proxy_weights.npz"
            generate_proxy_weights(output_path, seed=42)
            
            data = np.load(output_path)
            assert not np.any(np.isnan(data["A"]))
            assert not np.any(np.isnan(data["B"]))

class TestSaveWeights:
    def test_save_weights(self):
        """Test saving weights to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_weights.npz"
            data = {
                "A": np.random.randn(1024, 1024),
                "B": np.random.randn(1024, 4096)
            }
            save_weights(data, output_path)
            
            assert output_path.exists()
            loaded = np.load(output_path)
            assert np.array_equal(loaded["A"], data["A"])
            assert np.array_equal(loaded["B"], data["B"])

    def test_save_weights_creates_dir(self):
        """Test that save_weights creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "test_weights.npz"
            data = {
                "A": np.random.randn(1024, 1024),
                "B": np.random.randn(1024, 4096)
            }
            save_weights(data, output_path)
            
            assert output_path.exists()

class TestLoadRealWeights:
    @patch('src.ingestion.download_weights.load_dataset')
    def test_load_real_weights_success(self, mock_load_dataset):
        """Test loading real weights from dataset."""
        # Mock dataset
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter([
            {"weights_alfworld_A": np.random.randn(1024, 1024), "weights_alfworld_B": np.random.randn(1024, 4096)}
        ]))
        mock_load_dataset.return_value = mock_ds
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "real_weights.npz"
            from src.ingestion.download_weights import load_real_weights
            
            result = load_real_weights("test/dataset", "weights/alfworld", output_path)
            
            assert result is True
            assert output_path.exists()
            loaded = np.load(output_path)
            assert "weights_alfworld_A" in loaded.files
            assert "weights_alfworld_B" in loaded.files
    
    @patch('src.ingestion.download_weights.load_dataset')
    def test_load_real_weights_failure(self, mock_load_dataset):
        """Test that load_real_weights returns False on failure."""
        mock_load_dataset.side_effect = Exception("Dataset not found")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "real_weights.npz"
            from src.ingestion.download_weights import load_real_weights
            
            result = load_real_weights("test/dataset", "weights/alfworld", output_path)
            
            assert result is False
            assert not output_path.exists()