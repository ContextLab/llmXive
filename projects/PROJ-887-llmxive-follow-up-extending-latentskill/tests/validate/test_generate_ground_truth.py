"""
Unit tests for generate_ground_truth.py
"""

import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.validation.generate_ground_truth import (
    load_proxy_weights,
    interpolate_weights,
    save_ground_truth,
    generate_composite_ground_truth
)

class TestInterpolateWeights:
    """Tests for the interpolate_weights function."""

    def test_interpolation_alpha_0_5(self):
        """Test interpolation with alpha=0.5."""
        # Create mock weights
        weights_a = {
            'A': np.array([[1.0, 2.0], [3.0, 4.0]]),
            'B': np.array([[5.0, 6.0], [7.0, 8.0]]),
            'source': 'task_a'
        }
        weights_b = {
            'A': np.array([[9.0, 10.0], [11.0, 12.0]]),
            'B': np.array([[13.0, 14.0], [15.0, 16.0]]),
            'source': 'task_b'
        }

        result = interpolate_weights(weights_a, weights_b, alpha=0.5)

        # Expected: (0.5 * A) + (0.5 * B)
        expected_A = np.array([[5.0, 6.0], [7.0, 8.0]])
        expected_B = np.array([[9.0, 10.0], [11.0, 12.0]])

        assert np.allclose(result['A'], expected_A)
        assert np.allclose(result['B'], expected_B)
        assert result['alpha'] == 0.5

    def test_interpolation_alpha_0_0(self):
        """Test interpolation with alpha=0.0 (should equal weights_b)."""
        weights_a = {
            'A': np.array([[1.0, 2.0]]),
            'B': np.array([[3.0, 4.0]]),
            'source': 'task_a'
        }
        weights_b = {
            'A': np.array([[5.0, 6.0]]),
            'B': np.array([[7.0, 8.0]]),
            'source': 'task_b'
        }

        result = interpolate_weights(weights_a, weights_b, alpha=0.0)

        assert np.allclose(result['A'], weights_b['A'])
        assert np.allclose(result['B'], weights_b['B'])

    def test_interpolation_alpha_1_0(self):
        """Test interpolation with alpha=1.0 (should equal weights_a)."""
        weights_a = {
            'A': np.array([[1.0, 2.0]]),
            'B': np.array([[3.0, 4.0]]),
            'source': 'task_a'
        }
        weights_b = {
            'A': np.array([[5.0, 6.0]]),
            'B': np.array([[7.0, 8.0]]),
            'source': 'task_b'
        }

        result = interpolate_weights(weights_a, weights_b, alpha=1.0)

        assert np.allclose(result['A'], weights_a['A'])
        assert np.allclose(result['B'], weights_a['B'])

    def test_interpolation_dimension_mismatch(self):
        """Test that dimension mismatch raises ValueError."""
        weights_a = {
            'A': np.array([[1.0, 2.0]]),
            'B': np.array([[3.0, 4.0]]),
            'source': 'task_a'
        }
        weights_b = {
            'A': np.array([[5.0, 6.0, 7.0]]),  # Different shape
            'B': np.array([[7.0, 8.0]]),
            'source': 'task_b'
        }

        with pytest.raises(ValueError, match="Matrix A dimensions do not match"):
            interpolate_weights(weights_a, weights_b, alpha=0.5)

    def test_interpolation_invalid_alpha(self):
        """Test that invalid alpha raises ValueError."""
        weights_a = {
            'A': np.array([[1.0, 2.0]]),
            'B': np.array([[3.0, 4.0]]),
            'source': 'task_a'
        }
        weights_b = {
            'A': np.array([[5.0, 6.0]]),
            'B': np.array([[7.0, 8.0]]),
            'source': 'task_b'
        }

        with pytest.raises(ValueError, match="Alpha must be between 0.0 and 1.0"):
            interpolate_weights(weights_a, weights_b, alpha=1.5)

        with pytest.raises(ValueError, match="Alpha must be between 0.0 and 1.0"):
            interpolate_weights(weights_a, weights_b, alpha=-0.5)

class TestLoadProxyWeights:
    """Tests for the load_proxy_weights function."""

    def test_load_proxy_weights_success(self, tmp_path):
        """Test successful loading of proxy weights."""
        # Create a temporary directory structure
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)

        # Create mock proxy file
        mock_A = np.random.rand(10, 10)
        mock_B = np.random.rand(10, 10)
        file_path = raw_dir / "proxy_alfworld_weights.npz"
        np.savez(file_path, A=mock_A, B=mock_B)

        # Mock the PROJECT_ROOT path
        with patch('src.validation.generate_ground_truth.DATA_RAW_DIR', raw_dir):
            result = load_proxy_weights('alfworld')

            assert 'A' in result
            assert 'B' in result
            assert result['source'] == 'alfworld'
            assert np.allclose(result['A'], mock_A)
            assert np.allclose(result['B'], mock_B)

    def test_load_proxy_weights_missing_file(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)

        with patch('src.validation.generate_ground_truth.DATA_RAW_DIR', raw_dir):
            with pytest.raises(FileNotFoundError, match="Proxy weights file not found"):
                load_proxy_weights('alfworld')

    def test_load_proxy_weights_invalid_source(self, tmp_path):
        """Test that invalid source raises ValueError."""
        with pytest.raises(ValueError, match="Invalid source"):
            load_proxy_weights('invalid_source')

    def test_load_proxy_weights_missing_keys(self, tmp_path):
        """Test that missing A/B keys raises ValueError."""
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)

        # Create mock file with missing keys
        file_path = raw_dir / "proxy_alfworld_weights.npz"
        np.savez(file_path, A=np.random.rand(10, 10))  # Missing B

        with patch('src.validation.generate_ground_truth.DATA_RAW_DIR', raw_dir):
            with pytest.raises(ValueError, match="Invalid proxy weights format"):
                load_proxy_weights('alfworld')

class TestSaveGroundTruth:
    """Tests for the save_ground_truth function."""

    def test_save_ground_truth(self, tmp_path):
        """Test successful saving of ground truth."""
        output_path = tmp_path / "test_ground_truth.npz"

        weights = {
            'A': np.array([[1.0, 2.0]]),
            'B': np.array([[3.0, 4.0]]),
            'alpha': 0.5,
            'source_a': 'task_a',
            'source_b': 'task_b'
        }

        save_ground_truth(weights, output_path)

        assert output_path.exists()

        # Verify saved content
        data = np.load(output_path)
        assert 'A' in data
        assert 'B' in data
        assert 'alpha' in data
        assert 'source_a' in data
        assert 'source_b' in data
        assert np.allclose(data['A'], weights['A'])
        assert np.allclose(data['B'], weights['B'])
        assert data['alpha'] == weights['alpha']
        assert data['source_a'] == weights['source_a']
        assert data['source_b'] == weights['source_b']

class TestGenerateCompositeGroundTruth:
    """Tests for the main generate_composite_ground_truth function."""

    def test_generate_composite_ground_truth(self, tmp_path):
        """Test successful generation of composite ground truth."""
        # Create temporary directory structure
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)

        # Create mock proxy files
        mock_A_alfworld = np.random.rand(5, 5)
        mock_B_alfworld = np.random.rand(5, 5)
        mock_A_searchqa = np.random.rand(5, 5)
        mock_B_searchqa = np.random.rand(5, 5)

        np.savez(raw_dir / "proxy_alfworld_weights.npz", A=mock_A_alfworld, B=mock_B_alfworld)
        np.savez(raw_dir / "proxy_searchqa_weights.npz", A=mock_A_searchqa, B=mock_B_searchqa)

        # Mock paths
        with patch('src.validation.generate_ground_truth.DATA_RAW_DIR', raw_dir):
            with patch('src.validation.generate_ground_truth.DATA_PROCESSED_DIR', processed_dir):
                result = generate_composite_ground_truth(alpha=0.5)

                assert 'output_path' in result
                assert 'alpha' in result
                assert result['alpha'] == 0.5
                assert result['source_a'] == 'alfworld'
                assert result['source_b'] == 'searchqa'

                # Verify output file exists
                output_path = Path(result['output_path'])
                assert output_path.exists()

                # Verify content
                data = np.load(output_path)
                expected_A = 0.5 * mock_A_alfworld + 0.5 * mock_A_searchqa
                expected_B = 0.5 * mock_B_alfworld + 0.5 * mock_B_searchqa
                assert np.allclose(data['A'], expected_A)
                assert np.allclose(data['B'], expected_B)