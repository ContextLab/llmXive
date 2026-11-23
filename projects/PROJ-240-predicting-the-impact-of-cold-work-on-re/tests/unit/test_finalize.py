"""
tests/unit/test_finalize.py
Unit tests for code/finalize_dataset.py
"""
import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Add the project root to the path to allow imports
# Assuming tests are run from the project root or pytest is configured correctly
# The import path assumes the test is run within the project context
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.finalize_dataset import enforce_row_cap, load_engineered_data, save_final_dataset
from config import get_max_rows


class TestEnforceRowCap:
    def test_no_cap_needed(self):
        """Test that dataset smaller than max_rows is returned unchanged."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        result = enforce_row_cap(df, max_rows=10)
        assert len(result) == 3
        assert result.equals(df)

    def test_cap_applied(self):
        """Test that dataset larger than max_rows is truncated."""
        df = pd.DataFrame({"a": list(range(100))})
        result = enforce_row_cap(df, max_rows=10)
        assert len(result) == 10
        assert list(result["a"]) == list(range(10))

    def test_cap_none(self):
        """Test that max_rows=None keeps all rows."""
        df = pd.DataFrame({"a": list(range(100))})
        result = enforce_row_cap(df, max_rows=None)
        assert len(result) == 100

    def test_exact_match(self):
        """Test that dataset equal to max_rows is returned unchanged."""
        df = pd.DataFrame({"a": list(range(50))})
        result = enforce_row_cap(df, max_rows=50)
        assert len(result) == 50
        assert result.equals(df)


class TestSaveFinalDataset:
    def test_save_creates_file(self):
        """Test that save_final_dataset creates the file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test_output.csv"
            df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
            
            # Temporarily override the global path for testing
            # This is a bit hacky but works for unit testing file I/O without touching real paths
            import code.finalize_dataset as finalize_module
            original_path = finalize_module.FINAL_DATASET_PATH
            finalize_module.FINAL_DATASET_PATH = test_file
            
            try:
                save_final_dataset(df)
                assert test_file.exists()
                loaded_df = pd.read_csv(test_file)
                assert len(loaded_df) == 3
                assert list(loaded_df.columns) == ["a", "b"]
            finally:
                finalize_module.FINAL_DATASET_PATH = original_path

    def test_save_creates_directories(self):
        """Test that save_final_dataset creates parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            nested_path = tmp_path / "subdir" / "nested" / "test.csv"
            df = pd.DataFrame({"a": [1]})
            
            import code.finalize_dataset as finalize_module
            original_path = finalize_module.FINAL_DATASET_PATH
            finalize_module.FINAL_DATASET_PATH = nested_path
            
            try:
                save_final_dataset(df)
                assert nested_path.exists()
            finally:
                finalize_module.FINAL_DATASET_PATH = original_path


class TestLoadEngineeredData:
    def test_load_success(self):
        """Test loading a valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "engineered.csv"
            df_input = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
            df_input.to_csv(test_file, index=False)
            
            import code.finalize_dataset as finalize_module
            original_path = finalize_module.ENGINEERED_DATA_PATH
            finalize_module.ENGINEERED_DATA_PATH = test_file
            
            try:
                df_loaded = load_engineered_data()
                assert len(df_loaded) == 3
                assert list(df_loaded.columns) == ["x", "y"]
            finally:
                finalize_module.ENGINEERED_DATA_PATH = original_path

    def test_load_file_not_found(self):
        """Test that FileNotFoundError is raised if file doesn't exist."""
        import code.finalize_dataset as finalize_module
        original_path = finalize_module.ENGINEERED_DATA_PATH
        finalize_module.ENGINEERED_DATA_PATH = Path("/nonexistent/path/file.csv")
        
        try:
            with pytest.raises(FileNotFoundError):
                load_engineered_data()
        finally:
            finalize_module.ENGINEERED_DATA_PATH = original_path

    def test_load_empty_file(self):
        """Test that ValueError is raised if file is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "empty.csv"
            test_file.touch() # Create empty file
            
            import code.finalize_dataset as finalize_module
            original_path = finalize_module.ENGINEERED_DATA_PATH
            finalize_module.ENGINEERED_DATA_PATH = test_file
            
            try:
                with pytest.raises(ValueError):
                    load_engineered_data()
            finally:
                finalize_module.ENGINEERED_DATA_PATH = original_path
