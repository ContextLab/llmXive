"""
Contract test for the HarmonizedDataset schema validation.

This test suite verifies that the HarmonizedDataset data structure
adheres to the strict schema requirements defined in the project
specification, ensuring data integrity before downstream inference.
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import sys

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.loaders import HarmonizedDataset


class TestHarmonizedDatasetSchema:
    """Contract tests for HarmonizedDataset schema validation."""

    def test_harmonized_dataset_creation_valid(self):
        """Test that a valid HarmonizedDataset can be created."""
        # Valid input data
        sep_m = np.array([1e-5, 2e-5, 3e-5], dtype=np.float64)
        force_n = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        cov_matrix = np.eye(3, dtype=np.float64)
        
        dataset = HarmonizedDataset(
            separation_m=sep_m,
            force_N=force_n,
            covariance_matrix=cov_matrix,
            experiment_id="test_exp_001"
        )
        
        # Validate shapes
        assert dataset.separation_m.shape == (3,), "Separation shape mismatch"
        assert dataset.force_N.shape == (3,), "Force shape mismatch"
        assert dataset.covariance_matrix.shape == (3, 3), "Covariance shape mismatch"
        
        # Validate content
        assert dataset.experiment_id == "test_exp_001", "Experiment ID mismatch"
        assert np.allclose(dataset.separation_m, sep_m), "Separation data mismatch"
        assert np.allclose(dataset.force_N, force_n), "Force data mismatch"

    def test_harmonized_dataset_invalid_covariance_shape(self):
        """Test that mismatched covariance matrix dimensions raise ValueError."""
        sep_m = np.array([1e-5, 2e-5], dtype=np.float64)
        force_n = np.array([1.0, 2.0], dtype=np.float64)
        # Wrong shape: 3x3 for 2 data points
        cov_matrix = np.eye(3, dtype=np.float64)
        
        with pytest.raises(ValueError) as exc_info:
            HarmonizedDataset(
                separation_m=sep_m,
                force_N=force_n,
                covariance_matrix=cov_matrix,
                experiment_id="test_exp"
            )
        
        assert "covariance matrix shape" in str(exc_info.value).lower()

    def test_harmonized_dataset_non_square_covariance(self):
        """Test that non-square covariance matrices raise ValueError."""
        sep_m = np.array([1e-5, 2e-5, 3e-5], dtype=np.float64)
        force_n = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        # Non-square matrix
        cov_matrix = np.ones((3, 4), dtype=np.float64)
        
        with pytest.raises(ValueError) as exc_info:
            HarmonizedDataset(
                separation_m=sep_m,
                force_N=force_n,
                covariance_matrix=cov_matrix,
                experiment_id="test_exp"
            )
        
        assert "covariance matrix" in str(exc_info.value).lower()

    def test_harmonized_dataset_empty_arrays(self):
        """Test that empty arrays raise ValueError."""
        sep_m = np.array([], dtype=np.float64)
        force_n = np.array([], dtype=np.float64)
        cov_matrix = np.array([]).reshape(0, 0)
        
        # Depending on implementation, this might be allowed or disallowed.
        # Given the scientific context of "force-vs-separation", empty data is invalid.
        with pytest.raises(ValueError):
            HarmonizedDataset(
                separation_m=sep_m,
                force_N=force_n,
                covariance_matrix=cov_matrix,
                experiment_id="test_exp"
            )

    def test_harmonized_dataset_dtype_consistency(self):
        """Test that inputs are converted to float64."""
        sep_m = np.array([1e-5, 2e-5], dtype=np.float32)
        force_n = np.array([1.0, 2.0], dtype=np.float32)
        cov_matrix = np.eye(2, dtype=np.float32)
        
        dataset = HarmonizedDataset(
            separation_m=sep_m,
            force_N=force_n,
            covariance_matrix=cov_matrix,
            experiment_id="test_exp"
        )
        
        # Verify conversion to float64
        assert dataset.separation_m.dtype == np.float64, "Separation dtype not float64"
        assert dataset.force_N.dtype == np.float64, "Force dtype not float64"
        assert dataset.covariance_matrix.dtype == np.float64, "Covariance dtype not float64"

    def test_harmonized_dataset_metadata_handling(self):
        """Test that metadata is preserved correctly."""
        sep_m = np.array([1e-5], dtype=np.float64)
        force_n = np.array([1.0], dtype=np.float64)
        cov_matrix = np.eye(1, dtype=np.float64)
        metadata = {"source": "arXiv:2106.08611", "processed": True}
        
        dataset = HarmonizedDataset(
            separation_m=sep_m,
            force_N=force_n,
            covariance_matrix=cov_matrix,
            experiment_id="test_exp",
            metadata=metadata
        )
        
        assert dataset.metadata is not None
        assert dataset.metadata["source"] == "arXiv:2106.08611"