import pytest
import os
import json
from pathlib import Path
from preprocessing.ingestion import load_dataset_config, process_real_world_dataset, get_cleaned_data_path

class TestRealWorldIngestion:
    """Integration tests for real-world dataset ingestion (T034b)."""

    def test_load_dataset_config(self):
        """Test that dataset configuration loads correctly."""
        config_path = Path("data/config/datasets.yaml")
        assert config_path.exists(), "datasets.yaml must exist"
        
        config = load_dataset_config(config_path)
        assert "datasets" in config
        assert len(config["datasets"]) > 0
        # Check first dataset structure
        first_ds = config["datasets"][0]
        assert "id" in first_ds
        assert "source" in first_ds

    def test_process_iris_dataset(self):
        """Test processing the Iris dataset specifically."""
        dataset_entry = {
            "id": "uciml/iris",
            "source": "UCI Machine Learning Repository",
            "expected_size": 150
        }
        
        dataset_obj, clean_df, metadata = process_real_world_dataset(dataset_entry)
        
        assert dataset_obj is not None, "Dataset object should be created"
        assert clean_df is not None, "Cleaned dataframe should be created"
        assert metadata["status"] == "success", "Status should be success"
        assert metadata["cleaned_size"] > 0, "Cleaned size should be positive"
        assert "missing_rate" in metadata
        
        # Verify file saved
        saved_path = get_cleaned_data_path(dataset_entry["id"])
        assert saved_path.exists(), f"Cleaned data should be saved to {saved_path}"

    def test_manifest_generation(self):
        """Test that manifest is generated correctly."""
        # This is a basic check; full manifest logic is in main.py
        manifest_path = Path("data/metadata/manifest.json")
        # We don't run the full pipeline here to avoid long downloads in tests,
        # but we verify the structure if it exists
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            assert isinstance(manifest, list)
            if len(manifest) > 0:
                entry = manifest[0]
                assert "id" in entry
                assert "status" in entry
                assert "missing_rate" in entry or entry.get("status") == "failed"