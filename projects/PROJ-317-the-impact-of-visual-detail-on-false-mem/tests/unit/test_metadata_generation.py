"""
Unit tests for stimulus metadata generation (T017).
"""
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

import pytest
import yaml

from stimuli.metadata import (
    generate_metadata_for_image,
    save_metadata_as_yaml,
    load_metadata_from_yaml,
    generate_stimulus_metadata,
    StimulusMetadata
)
from config import get_stimuli_dir

class TestMetadataGeneration:
    """Tests for metadata generation functionality."""

    def test_generate_metadata_for_image_creates_required_fields(self):
        """Test that generate_metadata_for_image creates all required fields."""
        image_id = "test_img_001"
        image_path = Path("/fake/path/test_img_001.png")
        
        metadata = generate_metadata_for_image(image_id, image_path)
        
        # Verify all required fields are present
        assert metadata.id == image_id
        assert metadata.path == str(image_path)
        assert metadata.detail_level in ["low", "medium", "high", "baseline"]
        assert isinstance(metadata.object_list, list)
        assert isinstance(metadata.texture_settings, dict)
        assert metadata.timestamp is not None
        assert metadata.manipulation_timestamp is not None

    def test_manipulation_timestamp_is_iso_format(self):
        """Test that manipulation_timestamp is in ISO 8601 format."""
        image_id = "test_img_002"
        image_path = Path("/fake/path/test_img_002.png")
        
        metadata = generate_metadata_for_image(image_id, image_path)
        
        # Verify timestamp format
        try:
            datetime.fromisoformat(metadata.manipulation_timestamp.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail("manipulation_timestamp is not in valid ISO 8601 format")

    def test_save_metadata_as_yaml_creates_file(self, tmp_path):
        """Test that save_metadata_as_yaml creates a valid YAML file."""
        image_id = "test_img_003"
        image_path = tmp_path / "test_img_003.png"
        image_path.touch()  # Create dummy file
        
        metadata = generate_metadata_for_image(image_id, image_path)
        
        output_path = tmp_path / "test_img_003_metadata.yaml"
        save_metadata_as_yaml(metadata, output_path)
        
        assert output_path.exists()
        
        # Verify YAML content
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "manipulation_timestamp" in data
        assert data["id"] == image_id

    def test_load_metadata_from_yaml_reconstructs_object(self, tmp_path):
        """Test that load_metadata_from_yaml correctly reconstructs the object."""
        image_id = "test_img_004"
        image_path = tmp_path / "test_img_004.png"
        image_path.touch()
        
        original_metadata = generate_metadata_for_image(image_id, image_path)
        
        output_path = tmp_path / "test_img_004_metadata.yaml"
        save_metadata_as_yaml(original_metadata, output_path)
        
        loaded_metadata = load_metadata_from_yaml(output_path)
        
        assert loaded_metadata is not None
        assert loaded_metadata.id == original_metadata.id
        assert loaded_metadata.manipulation_timestamp == original_metadata.manipulation_timestamp

    def test_generate_stimulus_metadata_writes_file(self, tmp_path, monkeypatch):
        """Test that generate_stimulus_metadata writes to the correct location."""
        # Mock get_stimuli_dir to use tmp_path
        monkeypatch.setattr("stimuli.metadata.get_stimuli_dir", lambda: tmp_path)
        
        image_id = "test_img_005"
        image_path = tmp_path / "test_img_005.png"
        image_path.touch()
        
        generate_stimulus_metadata(image_id, image_path)
        
        output_path = tmp_path / f"{image_id}_metadata.yaml"
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "manipulation_timestamp" in data
        assert data["id"] == image_id

    def test_metadata_contains_manipulation_timestamp(self, tmp_path, monkeypatch):
        """Verification: Assert manipulation_timestamp is present in generated files."""
        monkeypatch.setattr("stimuli.metadata.get_stimuli_dir", lambda: tmp_path)
        
        image_id = "test_img_006"
        image_path = tmp_path / "test_img_006.png"
        image_path.touch()
        
        generate_stimulus_metadata(image_id, image_path)
        
        output_path = tmp_path / f"{image_id}_metadata.yaml"
        
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Core verification for T017
        assert "manipulation_timestamp" in data, "manipulation_timestamp is missing from metadata file"
        assert data["manipulation_timestamp"] is not None
        assert len(data["manipulation_timestamp"]) > 0