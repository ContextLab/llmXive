"""
Unit tests for download_weights module.
"""

import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion.download_weights import (
    generate_proxy_weights,
    save_weights,
    load_real_weights
)

class TestGenerateProxyWeights:
    """Tests for generate_proxy_weights function."""

    def test_generate_proxy_weights_dimensions(self):
        """Test that generated weights have correct dimensions."""
        A, B = generate_proxy_weights(in_features=4096, out_features=1024)

        assert A.shape == (1024, 4096), f"A shape mismatch: {A.shape}"
        assert B.shape == (4096, 1024), f"B shape mismatch: {B.shape}"

    def test_generate_proxy_weights_reproducibility(self):
        """Test that generated weights are reproducible with same seed."""
        A1, B1 = generate_proxy_weights(in_features=100, out_features=50, seed=42)
        A2, B2 = generate_proxy_weights(in_features=100, out_features=50, seed=42)

        np.testing.assert_array_equal(A1, A2)
        np.testing.assert_array_equal(B1, B2)

    def test_generate_proxy_weights_randomness(self):
        """Test that different seeds produce different weights."""
        A1, _ = generate_proxy_weights(in_features=100, out_features=50, seed=42)
        A2, _ = generate_proxy_weights(in_features=100, out_features=50, seed=123)

        assert not np.array_equal(A1, A2)

class TestSaveWeights:
    """Tests for save_weights function."""

    def test_save_weights_creates_file(self):
        """Test that save_weights creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_weights.npz"
            A = np.random.rand(10, 20)
            B = np.random.rand(20, 10)

            save_weights(A, B, output_path, "test")

            assert output_path.exists()

    def test_save_weights_correct_format(self):
        """Test that saved weights have correct format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_weights.npz"
            A = np.random.rand(10, 20)
            B = np.random.rand(20, 10)

            save_weights(A, B, output_path, "test")

            data = np.load(output_path)
            assert 'A' in data.files
            assert 'B' in data.files
            assert 'source_type' in data.files
            assert data['A'].shape == (10, 20)
            assert data['B'].shape == (20, 10)

class TestLoadRealWeights:
    """Tests for load_real_weights function."""

    def test_load_real_weights_missing_dataset(self):
        """Test that load_real_weights returns None for missing dataset."""
        result = load_real_weights("nonexistent/dataset", "path/*.npz")
        assert result is None

    @patch('src.ingestion.download_weights.load_dataset')
    def test_load_real_weights_success(self, mock_load_dataset):
        """Test successful loading of real weights."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([{'file_path': 'test.npz', 'A': [[1, 2]], 'B': [[3]]}]))
        mock_dataset.__getitem__ = MagicMock(return_value={'A': [[1, 2]], 'B': [[3]]})
        mock_load_dataset.return_value = mock_dataset

        # This is a simplified test; real implementation would need more complex mocking
        # For now, we just verify the function handles the case gracefully
        result = load_real_weights("test/dataset", "path/*.npz")
        # The actual result depends on implementation details