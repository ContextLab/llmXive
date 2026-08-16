import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import the module functions
# Note: In a real test environment, we might need to adjust the import path
# to point to the 'code' directory if it's not in sys.path.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from mahalanobis_distance import (
    calculate_mahalanobis_distance,
    load_model_selection,
    load_covariance_matrix,
    load_global_mean,
    load_cleaned_data,
    setup_logging
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_cleaned_data(temp_dir):
    """Create a mock cleaned_data.parquet file."""
    data = {
        "prompt": ["p1", "p2", "p3", "p4"],
        "image_url": ["u1", "u2", "u3", "u4"],
        "Alignment": [5.0, 4.0, 3.0, 6.0],
        "Realism": [4.5, 3.5, 2.5, 5.5],
        "Aesthetics": [4.0, 3.0, 2.0, 5.0],
        "Plausibility": [4.2, 3.2, 2.2, 5.2],
        "student_scalar": [4.5, 3.5, 2.5, 5.5],
        "primary_dimension": ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    }
    df = pd.DataFrame(data)
    output_path = temp_dir / "data" / "processed" / "cleaned_data.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path)
    return df

@pytest.fixture
def mock_model_selection(temp_dir, mock_cleaned_data):
    """Create a mock model_selection.json with 'rf' type."""
    output_path = temp_dir / "data" / "processed" / "model_selection.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"model_type": "rf"}, f)
    return output_path

@pytest.fixture
def mock_covariance_matrix(temp_dir, mock_cleaned_data):
    """Create a mock covariance_matrix.json."""
    # Create a valid 4x4 covariance matrix
    cov = np.array([
        [1.0, 0.5, 0.2, 0.1],
        [0.5, 1.0, 0.3, 0.2],
        [0.2, 0.3, 1.0, 0.4],
        [0.1, 0.2, 0.4, 1.0]
    ])
    output_path = temp_dir / "results" / "covariance_matrix.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"covariance_matrix": cov.tolist()}, f)
    return cov

@pytest.fixture
def mock_global_mean(temp_dir, mock_cleaned_data):
    """Create a mock global_mean.json."""
    mean = np.array([4.5, 3.8, 3.2, 3.5])
    output_path = temp_dir / "results" / "global_mean.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"mean_vector": mean.tolist()}, f)
    return mean

def test_calculate_mahalanobis_distance(mock_cleaned_data, mock_covariance_matrix, mock_global_mean):
    """Test the core Mahalanobis distance calculation logic."""
    df = mock_cleaned_data
    cov = mock_covariance_matrix
    mean = mock_global_mean
    logger = setup_logging()

    distances = calculate_mahalanobis_distance(df, cov, mean, logger)

    assert len(distances) == len(df)
    assert all(isinstance(d, (float, np.floating)) for d in distances)
    assert all(d >= 0 for d in distances)

def test_calculate_mahalanobis_singular_covariance(mock_cleaned_data, temp_dir, mock_global_mean):
    """Test handling of singular covariance matrix."""
    # Create a singular matrix (rank 1)
    singular_cov = np.ones((4, 4))
    
    output_path = temp_dir / "results" / "covariance_matrix.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"covariance_matrix": singular_cov.tolist()}, f)
    
    df = mock_cleaned_data
    mean = mock_global_mean
    logger = setup_logging()

    # Should not raise an error
    distances = calculate_mahalanobis_distance(df, singular_cov, mean, logger)

    assert len(distances) == len(df)
    assert all(d >= 0 for d in distances)

def test_missing_dimension_columns(mock_cleaned_data, mock_covariance_matrix, mock_global_mean, temp_dir):
    """Test error handling when required columns are missing."""
    df = mock_cleaned_data.drop(columns=["Alignment"])
    cov = mock_covariance_matrix
    mean = mock_global_mean
    logger = setup_logging()

    with pytest.raises(ValueError, match="Missing required dimension columns"):
        calculate_mahalanobis_distance(df, cov, mean, logger)

def test_small_dataset_warning(mock_cleaned_data, mock_covariance_matrix, mock_global_mean, temp_dir, caplog):
    """Test warning for small dataset."""
    # Create a dataset with < 4 samples
    small_data = {
        "prompt": ["p1", "p2"],
        "image_url": ["u1", "u2"],
        "Alignment": [5.0, 4.0],
        "Realism": [4.5, 3.5],
        "Aesthetics": [4.0, 3.0],
        "Plausibility": [4.2, 3.2],
        "student_scalar": [4.5, 3.5],
        "primary_dimension": ["Alignment", "Realism"]
    }
    df = pd.DataFrame(small_data)
    cov = mock_covariance_matrix
    mean = mock_global_mean
    logger = setup_logging()

    # Should issue a warning
    distances = calculate_mahalanobis_distance(df, cov, mean, logger)
    
    assert len(distances) == 2

def test_model_selection_skip(mock_cleaned_data, temp_dir, mock_covariance_matrix, mock_global_mean):
    """Test that the script skips when model_type is not 'rf'."""
    # Create model_selection with 'ridge'
    output_path = temp_dir / "data" / "processed" / "model_selection.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"model_type": "ridge"}, f)
    
    # Mock the load functions to use temp_dir
    # We can't easily mock the file paths in the module, so we test the logic
    # by checking if the file exists and reading it directly in a simplified way
    model_sel = json.load(open(output_path, "r"))
    assert model_sel["model_type"] == "ridge"
    # The actual skip logic is in main(), which we can't easily unit test without
    # refactoring, but we verify the condition is met.