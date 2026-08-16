import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from model_selection import load_cleaned_data, select_model_type, save_selection


class TestModelSelection:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data" / "processed"
            data_dir.mkdir(parents=True, exist_ok=True)
            yield data_dir

    def test_select_model_fail(self):
        assert select_model_type(10, None) == "fail"
        assert select_model_type(29, None) == "fail"

    def test_select_model_ridge(self):
        assert select_model_type(30, None) == "ridge"
        assert select_model_type(150, None) == "ridge"
        assert select_model_type(299, None) == "ridge"

    def test_select_model_rf(self):
        assert select_model_type(300, None) == "rf"
        assert select_model_type(1000, None) == "rf"

    def test_save_selection_fail(self, temp_dir, caplog):
        output_path = temp_dir / "model_selection.json"
        save_selection("fail", 20, "Critical Power Limitation: N < 30", None)
        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert data["status"] == "fail"
        assert data["model_type"] == "fail"
        assert data["sample_count"] == 20
        assert "reason" in data

    def test_save_selection_ridge(self, temp_dir, caplog):
        output_path = temp_dir / "model_selection.json"
        save_selection("ridge", 100, None, None)
        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert data["status"] == "success"
        assert data["model_type"] == "ridge"
        assert data["sample_count"] == 100

    def test_save_selection_rf(self, temp_dir, caplog):
        output_path = temp_dir / "model_selection.json"
        save_selection("rf", 500, None, None)
        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert data["status"] == "success"
        assert data["model_type"] == "rf"
        assert data["sample_count"] == 500

    def test_load_cleaned_data_missing(self, temp_dir, caplog):
        # Create a temp dir but do NOT create the parquet file
        fake_path = temp_dir / "nonexistent.parquet"
        with pytest.raises(FileNotFoundError):
            load_cleaned_data(None)

    def test_load_cleaned_data_success(self, temp_dir):
        # Create a dummy parquet
        df = pd.DataFrame({"col1": [1, 2, 3]})
        dummy_path = temp_dir / "cleaned_data.parquet"
        df.to_parquet(dummy_path)

        # Temporarily patch the function to use our path
        import model_selection as ms
        original_load = ms.load_cleaned_data

        def mock_load(logger):
            return pd.read_parquet(dummy_path)

        ms.load_cleaned_data = mock_load
        try:
            result = original_load(None) # Actually calls mock_load due to patching
            assert len(result) == 3
        finally:
            ms.load_cleaned_data = original_load