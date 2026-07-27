"""
Contract test for the HarmonizedDataset schema validation.
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.loaders import HarmonizedDataset

def test_harmonized_dataset_creation():
    """Test that a HarmonizedDataset can be created with valid data."""
    sep_m = np.array([1e-5, 2e-5, 3e-5])
    force_n = np.array([1.0, 2.0, 3.0])
    cov_matrix = np.eye(3)
    
    dataset = HarmonizedDataset(
      separation_m=sep_m,
      force_N=force_n,
      covariance_matrix=cov_matrix,
      experiment_id="test_exp"
    )
    
    assert dataset.separation_m.shape == (3,)
    assert dataset.force_N.shape == (3,)
    assert dataset.experiment_id == "test_exp"

def test_harmonized_dataset_invalid_covariance():
    """Test that invalid covariance matrix shapes raise errors."""
    sep_m = np.array([1e-5, 2e-5])
    force_n = np.array([1.0, 2.0])
    # Wrong shape for covariance
    cov_matrix = np.eye(3)
    
    with pytest.raises(ValueError):
        HarmonizedDataset(
            separation_m=sep_m,
            force_N=force_n,
            covariance_matrix=cov_matrix,
            experiment_id="test_exp"
        )
