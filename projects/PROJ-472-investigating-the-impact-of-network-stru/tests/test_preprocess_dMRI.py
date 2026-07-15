"""
Tests for code/data/preprocess_dMRI.py
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json

# Add code to path if running from tests
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.preprocess_dMRI import (
    generate_connectome_matrix,
    run_preprocessing_for_subject,
    download_parcellation,
    HCP_MMP_SHA256
)
from config import get_data_root

class TestGenerateConnectomeMatrix:
    def test_matrix_shape(self):
        """Test that the generated matrix has the correct shape."""
        num_nodes = 100
        matrix = generate_connectome_matrix(num_nodes=num_nodes, seed=42)
        assert matrix.shape == (num_nodes, num_nodes)

    def test_matrix_symmetric(self):
        """Test that the generated matrix is symmetric."""
        matrix = generate_connectome_matrix(num_nodes=50, seed=42)
        assert np.allclose(matrix, matrix.T)

    def test_diagonal_zero(self):
        """Test that the diagonal is zero."""
        matrix = generate_connectome_matrix(num_nodes=50, seed=42)
        assert np.allclose(np.diag(matrix), 0.0)

    def test_sparse(self):
        """Test that the matrix is sparse (density < 1.0)."""
        matrix = generate_connectome_matrix(num_nodes=100, seed=42)
        density = np.count_nonzero(matrix) / (matrix.shape[0] * matrix.shape[1])
        assert density < 1.0
        assert density > 0.0

    def test_non_negative(self):
        """Test that all values are non-negative."""
        matrix = generate_connectome_matrix(num_nodes=50, seed=42)
        assert np.all(matrix >= 0)

class TestPreprocessingPipeline:
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            raw_dir = tmpdir / "raw" / "dMRI"
            processed_dir = tmpdir / "processed" / "connectomes"
            parcellation_dir = tmpdir / "raw" / "parcellations"
            
            raw_dir.mkdir(parents=True)
            processed_dir.mkdir(parents=True)
            parcellation_dir.mkdir(parents=True)
            
            # Create a dummy subject directory
            subject_dir = raw_dir / "sub-001"
            subject_dir.mkdir(parents=True)
            # Create a dummy tck file
            (subject_dir / "streamlines.tck").write_text("FAKE_TCK")
            
            yield {
                "raw_dir": raw_dir,
                "processed_dir": processed_dir,
                "parcellation_dir": parcellation_dir,
                "subject_id": "sub-001"
            }

    def test_run_preprocessing_creates_output(self, temp_dirs):
        """Test that preprocessing creates the output CSV."""
        result = run_preprocessing_for_subject(
            subject_id=temp_dirs["subject_id"],
            raw_dir=temp_dirs["raw_dir"],
            processed_dir=temp_dirs["processed_dir"],
            parcellation_path=temp_dirs["parcellation_dir"] / "HCP_MMP1.0.nii.gz",
            num_nodes=360
        )
        
        assert result["status"] == "success"
        output_file = Path(result["output_file"])
        assert output_file.exists()
        
        # Verify CSV content
        df = pd.read_csv(output_file, header=None)
        assert df.shape[0] == 360
        assert df.shape[1] == 360

    def test_run_preprocessing_returns_correct_info(self, temp_dirs):
        """Test that the result dictionary contains expected keys."""
        result = run_preprocessing_for_subject(
            subject_id=temp_dirs["subject_id"],
            raw_dir=temp_dirs["raw_dir"],
            processed_dir=temp_dirs["processed_dir"],
            parcellation_path=temp_dirs["parcellation_dir"] / "HCP_MMP1.0.nii.gz",
            num_nodes=360
        )
        
        assert "subject_id" in result
        assert "status" in result
        assert "output_file" in result
        assert "matrix_shape" in result
        assert "non_zero_entries" in result
        assert result["matrix_shape"] == (360, 360)