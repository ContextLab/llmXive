"""
Integration test to verify conftest.py fixtures work correctly.

This is a lightweight test to ensure the shared fixtures can be imported
and used without errors.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path


def test_project_root_fixture(project_root):
    """Verify project root is a valid Path object."""
    assert isinstance(project_root, Path)
    assert project_root.exists()


def test_temp_output_dir_fixture(temp_output_dir):
    """Verify temp directory is created and cleaned up."""
    assert temp_output_dir.exists()
    # Create a dummy file
    test_file = temp_output_dir / "test.txt"
    test_file.write_text("test")
    assert test_file.exists()


def test_sample_entropy_vector_fixture(sample_entropy_vector):
    """Verify sample entropy vector is a valid numpy array."""
    assert isinstance(sample_entropy_vector, np.ndarray)
    assert sample_entropy_vector.dtype == np.float64
    assert len(sample_entropy_vector) == 500
    assert not np.any(np.isnan(sample_entropy_vector))


def test_sample_multiscale_data_fixture(sample_multiscale_data):
    """Verify multiscale data is a valid 2D array."""
    assert isinstance(sample_multiscale_data, np.ndarray)
    assert sample_multiscale_data.dtype == np.float64
    assert sample_multiscale_data.shape == (5, 200)


def test_sample_parcels_data_fixture(sample_parcels_data):
    """Verify parcel data is a valid DataFrame with expected columns."""
    assert isinstance(sample_parcels_data, pd.DataFrame)
    assert "parcel_id" in sample_parcels_data.columns
    assert "entropy_value" in sample_parcels_data.columns
    assert "subject_id" in sample_parcels_data.columns
    assert len(sample_parcels_data) == 360
    # Check for NaNs
    assert sample_parcels_data["entropy_value"].isna().sum() > 0


def test_sample_network_mapping_fixture(sample_network_mapping):
    """Verify network mapping is a valid dictionary."""
    assert isinstance(sample_network_mapping, dict)
    assert "DMN" in sample_network_mapping
    assert "FPN" in sample_network_mapping
    assert "CON" in sample_network_mapping
    assert len(sample_network_mapping["DMN"]) == 60


def test_mock_phenotype_csv_fixture(mock_phenotype_csv, temp_output_dir):
    """Verify mock phenotype CSV is created and readable."""
    assert mock_phenotype_csv.exists()
    df = pd.read_csv(mock_phenotype_csv)
    assert "subject_id" in df.columns
    assert "age" in df.columns
    assert "creative_score" in df.columns
    assert len(df) == 10
