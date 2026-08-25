"""
Unit tests for the derive_bbox module (Task T002).
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.derive_bbox import calculate_bounding_box, save_bounding_box, load_moral_machine_data

class TestCalculateBoundingBox:
    def test_basic_calculation(self):
        """Test that bounding box is calculated correctly from valid data."""
        data = {
            'latitude': [10.0, 20.0, 30.0],
            'longitude': [-5.0, 0.0, 5.0]
        }
        df = pd.DataFrame(data)
        
        bbox = calculate_bounding_box(df)
        
        assert bbox['min_lat'] == 10.0
        assert bbox['max_lat'] == 30.0
        assert bbox['min_lon'] == -5.0
        assert bbox['max_lon'] == 5.0
        
        assert isinstance(bbox['min_lat'], float)
        assert isinstance(bbox['max_lat'], float)
        assert isinstance(bbox['min_lon'], float)
        assert isinstance(bbox['max_lon'], float)

    def test_with_missing_values(self):
        """Test that rows with missing coordinates are ignored."""
        data = {
            'latitude': [10.0, None, 30.0],
            'longitude': [-5.0, 0.0, None]
        }
        df = pd.DataFrame(data)
        
        # Only the first row is fully valid
        bbox = calculate_bounding_box(df)
        
        assert bbox['min_lat'] == 10.0
        assert bbox['max_lat'] == 10.0
        assert bbox['min_lon'] == -5.0
        assert bbox['max_lon'] == -5.0

    def test_empty_valid_data_raises(self):
        """Test that an error is raised if no valid coordinates exist."""
        data = {
            'latitude': [None, None],
            'longitude': [None, None]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="No valid latitude/longitude"):
            calculate_bounding_box(df)

class TestSaveBoundingBox:
    def test_save_and_load(self):
        """Test that bounding box is saved correctly and can be loaded back."""
        bbox = {
            "min_lat": 10.0,
            "max_lat": 20.0,
            "min_lon": -5.0,
            "max_lon": 5.0
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_bbox.json"
            save_bounding_box(bbox, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                loaded_bbox = json.load(f)
            
            assert loaded_bbox == bbox

class TestLoadMoralMachineData:
    def test_load_compressed(self, tmp_path):
        """Test loading a compressed CSV file."""
        # Create a temporary compressed CSV
        test_data = pd.DataFrame({
            'latitude': [1.0, 2.0],
            'longitude': [1.0, 2.0]
        })
        csv_path = tmp_path / "test.csv.gz"
        test_data.to_csv(csv_path, compression='gzip', index=False)
        
        # Temporarily override the path
        original_get_path_env_override = None
        # We cannot easily mock the import inside the module, so we test the logic
        # by creating the file where the default expects it would be, or by
        # ensuring the function handles the file correctly if we pass it directly.
        # Since load_moral_machine_data uses get_path_env_override, we rely on
        # the environment variable or the default path.
        
        # For this unit test, we verify the function's behavior with a known file
        # by temporarily setting the env var.
        os.environ["MORAL_MACHINE_DATA_PATH"] = str(csv_path)
        try:
            df = load_moral_machine_data()
            assert len(df) == 2
            assert 'latitude' in df.columns
            assert 'longitude' in df.columns
        finally:
            if "MORAL_MACHINE_DATA_PATH" in os.environ:
                del os.environ["MORAL_MACHINE_DATA_PATH"]

    def test_load_uncompressed(self, tmp_path):
        """Test loading an uncompressed CSV file."""
        test_data = pd.DataFrame({
            'latitude': [1.0, 2.0],
            'longitude': [1.0, 2.0]
        })
        csv_path = tmp_path / "test.csv"
        test_data.to_csv(csv_path, index=False)
        
        os.environ["MORAL_MACHINE_DATA_PATH"] = str(csv_path)
        try:
            df = load_moral_machine_data()
            assert len(df) == 2
        finally:
            if "MORAL_MACHINE_DATA_PATH" in os.environ:
                del os.environ["MORAL_MACHINE_DATA_PATH"]

    def test_sample_size(self, tmp_path):
        """Test that sample_size parameter works."""
        test_data = pd.DataFrame({
            'latitude': list(range(100)),
            'longitude': list(range(100))
        })
        csv_path = tmp_path / "test.csv"
        test_data.to_csv(csv_path, index=False)
        
        os.environ["MORAL_MACHINE_DATA_PATH"] = str(csv_path)
        try:
            df = load_moral_machine_data(sample_size=10)
            assert len(df) == 10
        finally:
            if "MORAL_MACHINE_DATA_PATH" in os.environ:
                del os.environ["MORAL_MACHINE_DATA_PATH"]

    def test_missing_file_raises(self):
        """Test that FileNotFoundError is raised if file doesn't exist."""
        # Ensure the env var is not set or points to non-existent file
        os.environ["MORAL_MACHINE_DATA_PATH"] = "/nonexistent/path/file.csv.gz"
        try:
            with pytest.raises(FileNotFoundError):
                load_moral_machine_data()
        finally:
            if "MORAL_MACHINE_DATA_PATH" in os.environ:
                del os.environ["MORAL_MACHINE_DATA_PATH"]

    def test_missing_columns_raises(self, tmp_path):
        """Test that ValueError is raised if required columns are missing."""
        test_data = pd.DataFrame({
            'lat': [1.0, 2.0],
            'lon': [1.0, 2.0]
        })
        csv_path = tmp_path / "test.csv"
        test_data.to_csv(csv_path, index=False)
        
        os.environ["MORAL_MACHINE_DATA_PATH"] = str(csv_path)
        try:
            with pytest.raises(ValueError, match="Missing required columns"):
                load_moral_machine_data()
        finally:
            if "MORAL_MACHINE_DATA_PATH" in os.environ:
                del os.environ["MORAL_MACHINE_DATA_PATH"]
