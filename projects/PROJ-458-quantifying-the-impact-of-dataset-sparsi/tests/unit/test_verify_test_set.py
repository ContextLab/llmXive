"""
Unit tests for verify_test_set.py
"""
import os
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys_path = str(project_root / "code")
if sys_path not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_path)

from verify_test_set import verify_test_set


class TestVerifyTestSet:
    @pytest.fixture
    def temp_files(self):
        """Create temporary files for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create raw pool
            raw_pool_path = tmpdir / "raw_pool.csv"
            raw_data = {
                "material_id": ["mp-1", "mp-2", "mp-3", "mp-4", "mp-5"],
                "composition": ["Si", "SiO2", "Al2O3", "Fe2O3", "Cu"],
                "formation_energy": [-1.0, -2.0, -3.0, -4.0, -5.0],
                "dft_computed": [True, True, True, True, True],
            }
            raw_df = pd.DataFrame(raw_data)
            raw_df.to_csv(raw_pool_path, index=False)

            # Create test set (subset of raw pool)
            test_set_path = tmpdir / "test_set.csv"
            test_data = {
                "material_id": ["mp-1", "mp-3", "mp-5"],
                "composition": ["Si", "Al2O3", "Cu"],
                "formation_energy": [-1.0, -3.0, -5.0],
                "dft_computed": [True, True, True],
            }
            test_df = pd.DataFrame(test_data)
            test_df.to_csv(test_set_path, index=False)

            # Create test set indices
            indices_path = tmpdir / "test_set_indices.csv"
            indices_data = {"index": [0, 2, 4]}
            indices_df = pd.DataFrame(indices_data)
            indices_df.to_csv(indices_path, index=False)

            # Metadata output path
            metadata_path = tmpdir / "test_set_metadata.json"

            yield {
                "raw_pool_path": str(raw_pool_path),
                "test_set_path": str(test_set_path),
                "indices_path": str(indices_path),
                "metadata_path": str(metadata_path),
            }

    def test_verify_test_set_success(self, temp_files):
        """Test that verification passes for valid test set."""
        result = verify_test_set(
            temp_files["raw_pool_path"],
            temp_files["test_set_path"],
            temp_files["indices_path"],
            temp_files["metadata_path"],
        )

        assert result["verification_status"] == "passed"
        assert result["row_count"] == 3
        assert "checksum" in result
        assert os.path.exists(temp_files["metadata_path"])

        # Verify JSON content
        with open(temp_files["metadata_path"], "r") as f:
            metadata = json.load(f)
        assert metadata["row_count"] == 3
        assert metadata["verification_status"] == "passed"

    def test_verify_test_set_missing_indices(self, temp_files):
        """Test that verification fails when test set has indices not in raw pool."""
        # Modify test set to have an index not in raw pool
        test_df = pd.read_csv(temp_files["test_set_path"])
        test_df.loc[len(test_df)] = {
            "material_id": "mp-99",
            "composition": "X",
            "formation_energy": -99.0,
            "dft_computed": True,
        }
        test_df.to_csv(temp_files["test_set_path"], index=False)

        # Modify indices to include a new index
        indices_df = pd.read_csv(temp_files["indices_path"])
        indices_df.loc[len(indices_df)] = {"index": 99}
        indices_df.to_csv(temp_files["indices_path"], index=False)

        with pytest.raises(ValueError) as exc_info:
            verify_test_set(
                temp_files["raw_pool_path"],
                temp_files["test_set_path"],
                temp_files["indices_path"],
                temp_files["metadata_path"],
            )

        assert "not found in raw pool" in str(exc_info.value)

    def test_verify_test_set_row_count_mismatch(self, temp_files):
        """Test that verification fails when row count doesn't match indices."""
        # Add an extra row to test set but not to indices
        test_df = pd.read_csv(temp_files["test_set_path"])
        test_df.loc[len(test_df)] = {
            "material_id": "mp-99",
            "composition": "X",
            "formation_energy": -99.0,
            "dft_computed": True,
        }
        test_df.to_csv(temp_files["test_set_path"], index=False)

        with pytest.raises(ValueError) as exc_info:
            verify_test_set(
                temp_files["raw_pool_path"],
                temp_files["test_set_path"],
                temp_files["indices_path"],
                temp_files["metadata_path"],
            )

        assert "row count mismatch" in str(exc_info.value)