import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from code.global_covariance import (
    calculate_global_covariance_and_eigenvalue,
    extract_teacher_scores_matrix,
    load_cleaned_data,
    save_covariance_matrix,
    save_dominant_eigenvalue,
)


@pytest.fixture
def sample_cleaned_data(tmp_path):
    """Create a minimal valid cleaned_data.parquet file."""
    data = {
        "prompt": ["p1", "p2", "p3", "p4"],
        "image_url": ["u1", "u2", "u3", "u4"],
        "Alignment": [5.0, 6.0, 4.0, 5.5],
        "Realism": [4.0, 5.0, 3.0, 4.5],
        "Aesthetics": [6.0, 7.0, 5.0, 6.5],
        "Plausibility": [5.0, 5.5, 4.5, 5.0],
        "student_scalar": [3.0, 3.5, 2.5, 3.2],
        "primary_dimension": ["Alignment", "Realism", "Aesthetics", "Plausibility"],
        "fidelity_loss": [1.0, 0.5, 1.5, 0.8],
    }
    df = pd.DataFrame(data)
    output_path = tmp_path / "cleaned_data.parquet"
    df.to_parquet(output_path)
    return str(output_path)


def test_load_cleaned_data(sample_cleaned_data):
    df = load_cleaned_data(sample_cleaned_data, None)
    assert len(df) == 4
    assert "Alignment" in df.columns


def test_extract_teacher_scores_matrix(sample_cleaned_data):
    df = load_cleaned_data(sample_cleaned_data, None)
    matrix = extract_teacher_scores_matrix(df, None)
    assert matrix.shape == (4, 4)
    assert matrix.dtype == np.float64


def test_calculate_global_covariance_and_eigenvalue(sample_cleaned_data):
    df = load_cleaned_data(sample_cleaned_data, None)
    matrix = extract_teacher_scores_matrix(df, None)
    cov, eig = calculate_global_covariance_and_eigenvalue(matrix, None)
    assert cov.shape == (4, 4)
    assert isinstance(eig, float)
    assert eig > 0  # Covariance matrices from real data usually have positive dominant eigenvalue


def test_insufficient_samples_raises_error(sample_cleaned_data):
    # Create a dataset with only 2 rows
    data = {
        "Alignment": [1.0, 2.0],
        "Realism": [1.0, 2.0],
        "Aesthetics": [1.0, 2.0],
        "Plausibility": [1.0, 2.0],
    }
    df = pd.DataFrame(data)
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        temp_path = f.name
    df.to_parquet(temp_path)

    try:
        matrix = extract_teacher_scores_matrix(df, None)
        with pytest.raises(RuntimeError, match="Insufficient samples"):
            calculate_global_covariance_and_eigenvalue(matrix, None)
    finally:
        os.unlink(temp_path)


def test_save_covariance_matrix(tmp_path):
    cov = np.array([[1.0, 0.5], [0.5, 2.0]])
    output_path = str(tmp_path / "cov.json")
    save_covariance_matrix(cov, output_path, None)

    assert os.path.exists(output_path)
    with open(output_path) as f:
        data = json.load(f)
    assert data["shape"] == [2, 2]
    assert np.allclose(data["values"], cov.tolist())


def test_save_dominant_eigenvalue(tmp_path):
    eig = 1.5
    output_path = str(tmp_path / "eig.json")
    save_dominant_eigenvalue(eig, output_path, None)

    assert os.path.exists(output_path)
    with open(output_path) as f:
        data = json.load(f)
    assert abs(data["dominant_eigenvalue"] - eig) < 1e-6
