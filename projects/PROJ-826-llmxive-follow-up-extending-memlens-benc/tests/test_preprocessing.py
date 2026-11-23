import pytest
import json
import os
import tempfile
from pathlib import Path
import numpy as np

# Import the functions to test
from preprocessing import (
    load_memlens_dataset,
    construct_fine_store,
    validate_schema,
    get_text_embedding
)

class TestFineStoreConstruction:
    """Test cases for Fine store construction with coordinate exclusion."""

    @pytest.fixture
    def sample_dataset(self):
        """Create a sample dataset with object captions and bounding boxes."""
        return [
            {
                "id": 1,
                "object_captions": ["a red car", "a blue bicycle"],
                "bounding_boxes": [
                    [100, 200, 150, 250],  # [x1, y1, x2, y2]
                    [300, 400, 350, 450]
                ],
                "detection_status": "success",
                "source": "test_source",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "object_captions": ["a person walking"],
                "bounding_boxes": [[50, 50, 100, 200]],
                "detection_status": "success",
                "source": "test_source",
                "timestamp": "2024-01-01T01:00:00Z"
            },
            {
                "id": 3,
                "object_captions": [],
                "bounding_boxes": [],
                "detection_status": "zero_detection",
                "source": "test_source",
                "timestamp": "2024-01-01T02:00:00Z"
            },
            {
                "id": 4,
                "object_captions": ["a dog"],
                "bounding_boxes": [[10, 10, 50, 50]],
                "detection_status": "fallback",
                "source": "test_source",
                "timestamp": "2024-01-01T03:00:00Z"
            }
        ]

    def test_fine_store_creates_entries(self, sample_dataset):
        """Test that Fine store is created with correct entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "fine_store.json")
            store = construct_fine_store(sample_dataset, output_path)
            
            # Should only include entries with successful detection
            assert store["metadata"]["total_entries"] == 2
            assert len(store["entries"]) == 2

    def test_coordinates_excluded_from_embedding(self, sample_dataset):
        """Test that bounding box coordinates are NOT used in embeddings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "fine_store.json")
            store = construct_fine_store(sample_dataset, output_path)
            
            for entry in store["entries"]:
                # Check that embedding exists and is a list of floats
                assert "embedding" in entry
                assert isinstance(entry["embedding"], list)
                assert all(isinstance(x, float) for x in entry["embedding"])
                
                # Verify coordinates are in metadata but NOT in the embedding vector
                assert "metadata" in entry
                assert "bounding_boxes" in entry["metadata"]
                
                # Critical check: coordinates must be marked as excluded from similarity
                assert entry["metadata"].get("coordinates_excluded_from_similarity") is True

    def test_detection_status_filtering(self, sample_dataset):
        """Test that entries with fallback/zero_detection are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "fine_store.json")
            store = construct_fine_store(sample_dataset, output_path)
            
            # Only entries with "success" status should be included
            for entry in store["entries"]:
                assert entry["metadata"]["detection_status"] == "success"
            
            # Entries 3 and 4 (zero_detection and fallback) should be excluded
            entry_ids = [entry["id"] for entry in store["entries"]]
            assert 3 not in entry_ids
            assert 4 not in entry_ids

    def test_combined_caption_generation(self, sample_dataset):
        """Test that object captions are combined correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "fine_store.json")
            store = construct_fine_store(sample_dataset, output_path)
            
            # First entry should have combined caption from both objects
            first_entry = store["entries"][0]
            assert "combined_caption" in first_entry
            assert "red car" in first_entry["combined_caption"]
            assert "blue bicycle" in first_entry["combined_caption"]

    def test_store_structure(self, sample_dataset):
        """Test that the store has the correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "fine_store.json")
            store = construct_fine_store(sample_dataset, output_path)
            
            assert store["type"] == "fine"
            assert "entries" in store
            assert "metadata" in store
            assert store["metadata"]["embedding_model"] == "all-MiniLM-L6-v2"
            assert "total_entries" in store["metadata"]

    def test_file_persistence(self, sample_dataset):
        """Test that the store is correctly saved to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "fine_store.json")
            construct_fine_store(sample_dataset, output_path)
            
            # Verify file exists and can be loaded
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                loaded_store = json.load(f)
            
            assert loaded_store["type"] == "fine"
            assert len(loaded_store["entries"]) == 2

class TestValidation:
    """Test validation functions."""

    def test_validate_schema_pass(self):
        """Test schema validation with valid data."""
        data = {"name": "test", "value": 123}
        schema = {"required": ["name", "value"]}
        assert validate_schema(data, schema) is True

    def test_validate_schema_fail(self):
        """Test schema validation with missing required fields."""
        data = {"name": "test"}
        schema = {"required": ["name", "value"]}
        assert validate_schema(data, schema) is False
