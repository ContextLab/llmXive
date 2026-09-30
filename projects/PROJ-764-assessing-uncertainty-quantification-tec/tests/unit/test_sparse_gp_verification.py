import os
import pytest
from pathlib import Path
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.sparse_gp import verify_dependencies, main

class TestSparseGPVerification:
    """
    Unit tests for T015a: Sparse GP Verification.
    Ensures that the verification logic correctly identifies missing artifacts
    and raises errors as required.
    """

    def test_missing_test_features_raises_error(self, tmp_path):
        """Test that missing features_test_20pca.csv raises FileNotFoundError."""
        # Create a temp directory structure that mimics the project but lacks the file
        data_processed = tmp_path / "data" / "processed"
        data_processed.mkdir(parents=True)
        
        # Create the transformer file (to simulate partial setup)
        transformer_path = data_processed / "pca_transformer.pkl"
        transformer_path.touch()
        
        # Do NOT create features_test_20pca.csv

        # Change CWD to tmp_path to simulate the check
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(FileNotFoundError, match="Missing required artifacts"):
                verify_dependencies()
        finally:
            os.chdir(old_cwd)

    def test_missing_transformer_raises_error(self, tmp_path):
        """Test that missing pca_transformer.pkl raises FileNotFoundError."""
        data_processed = tmp_path / "data" / "processed"
        data_processed.mkdir(parents=True)
        
        # Create the CSV file
        csv_path = data_processed / "features_test_20pca.csv"
        csv_path.touch()
        
        # Do NOT create the transformer file

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(FileNotFoundError, match="Missing required artifacts"):
                verify_dependencies()
        finally:
            os.chdir(old_cwd)

    def test_all_artifacts_present_returns_true(self, tmp_path):
        """Test that verification passes when all artifacts exist."""
        data_processed = tmp_path / "data" / "processed"
        data_processed.mkdir(parents=True)
        
        # Create both required files
        (data_processed / "features_test_20pca.csv").touch()
        (data_processed / "pca_transformer.pkl").touch()

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Should not raise
            result = verify_dependencies()
            assert result is True
        finally:
            os.chdir(old_cwd)
