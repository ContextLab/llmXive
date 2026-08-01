"""
Unit tests for T017: Stimulus Metadata Generation
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import TestCase

import yaml

# Import the module under test
from code.stimuli.metadata import (
    StimulusMetadata,
    generate_metadata_for_image,
    save_metadata_as_yaml,
    load_metadata_from_yaml,
    generate_stimulus_metadata
)

class TestStimulusMetadata(TestCase):
    """Tests for the StimulusMetadata dataclass and generation functions."""

    def test_generate_metadata_structure(self):
        """Test that generated metadata has all required fields."""
        metadata = generate_metadata_for_image(
            image_id="test_001",
            image_path=Path("/fake/path/test_001.jpg"),
            object_list=["car", "tree"],
            complexity_score=0.5
        )

        self.assertEqual(metadata.id, "test_001")
        self.assertEqual(metadata.object_list, ["car", "tree"])
        self.assertEqual(metadata.complexity_score, 0.5)
        self.assertIn("detail_level", metadata.__dict__)
        self.assertIn("texture_settings", metadata.__dict__)
        self.assertIn("timestamp", metadata.__dict__)
        self.assertIn("manipulation_timestamp", metadata.__dict__)
        
        # Verify ISO 8601 format for timestamps
        try:
            datetime.fromisoformat(metadata.timestamp)
            datetime.fromisoformat(metadata.manipulation_timestamp)
        except ValueError:
            self.fail("Timestamps are not in ISO 8601 format")

    def test_manipulation_timestamp_present(self):
        """Test that manipulation_timestamp is present (T017 requirement)."""
        metadata = generate_metadata_for_image(
            image_id="test_002",
            image_path=Path("/fake/path/test_002.jpg"),
            object_list=["dog"],
            complexity_score=0.3
        )
        
        self.assertIsNotNone(metadata.manipulation_timestamp)
        self.assertIsInstance(metadata.manipulation_timestamp, str)
        self.assertGreater(len(metadata.manipulation_timestamp), 0)

    def test_save_and_load_yaml(self):
        """Test saving and loading metadata from YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            metadata = generate_metadata_for_image(
                image_id="test_003",
                image_path=Path("/fake/path/test_003.jpg"),
                object_list=["bird", "sky"],
                complexity_score=0.7
            )
            
            # Save
            saved_path = save_metadata_as_yaml(metadata, output_dir)
            self.assertTrue(saved_path.exists())
            
            # Load
            loaded_metadata = load_metadata_from_yaml(saved_path)
            
            self.assertEqual(loaded_metadata.id, metadata.id)
            self.assertEqual(loaded_metadata.object_list, metadata.object_list)
            self.assertEqual(loaded_metadata.complexity_score, metadata.complexity_score)
            self.assertEqual(loaded_metadata.detail_level, metadata.detail_level)
            self.assertEqual(loaded_metadata.manipulation_timestamp, metadata.manipulation_timestamp)

    def test_yaml_content_structure(self):
        """Test that the YAML file contains all required keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            metadata = generate_metadata_for_image(
                image_id="test_004",
                image_path=Path("/fake/path/test_004.jpg"),
                object_list=["house", "road", "person"],
                complexity_score=0.6
            )
            
            saved_path = save_metadata_as_yaml(metadata, output_dir)
            
            with open(saved_path, 'r') as f:
                data = yaml.safe_load(f)
            
            required_keys = [
                'id', 'detail_level', 'object_list', 'texture_settings',
                'timestamp', 'manipulation_timestamp'
            ]
            
            for key in required_keys:
                self.assertIn(key, data, f"Missing required key: {key}")
            
            # Verify manipulation_timestamp is a string
            self.assertIsInstance(data['manipulation_timestamp'], str)
            self.assertGreater(len(data['manipulation_timestamp']), 0)

    def test_texture_settings_structure(self):
        """Test that texture_settings is a dictionary with expected keys."""
        metadata = generate_stimulus_metadata(
            image_id="test_005",
            image_path="fake.jpg",
            object_list=["cat"],
            complexity_score=0.4
        )
        
        self.assertIsInstance(metadata.texture_settings, dict)
        self.assertIn("blur_radius", metadata.texture_settings)
        self.assertIn("sharpen", metadata.texture_settings)
        self.assertIn("noise_level", metadata.texture_settings)
        self.assertIn("contrast", metadata.texture_settings)

class TestMetadataIntegration(TestCase):
    """Integration tests for metadata generation workflow."""

    def test_multiple_images_metadata(self):
        """Test generating metadata for multiple images."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            images = [
                ("img_001", ["car", "tree"], 0.5),
                ("img_002", ["dog", "ball"], 0.3),
                ("img_003", ["person", "building"], 0.7),
            ]
            
            for img_id, objects, complexity in images:
                metadata = generate_metadata_for_image(
                    image_id=img_id,
                    image_path=Path(f"/fake/{img_id}.jpg"),
                    object_list=objects,
                    complexity_score=complexity
                )
                save_metadata_as_yaml(metadata, output_dir)
            
            # Verify all files exist
            for img_id, _, _ in images:
                filepath = output_dir / f"{img_id}_metadata.yaml"
                self.assertTrue(filepath.exists())
                
                # Verify manipulation_timestamp
                with open(filepath, 'r') as f:
                    data = yaml.safe_load(f)
                self.assertIn('manipulation_timestamp', data)
                self.assertIsNotNone(data['manipulation_timestamp'])

    def test_empty_object_list(self):
        """Test handling of empty object list."""
        metadata = generate_metadata_for_image(
            image_id="test_empty",
            image_path=Path("/fake/empty.jpg"),
            object_list=[],
            complexity_score=0.0
        )
        
        self.assertEqual(metadata.object_list, [])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            save_metadata_as_yaml(metadata, Path(tmpdir))
            # Should not raise
            loaded = load_metadata_from_yaml(Path(tmpdir) / "test_empty_metadata.yaml")
            self.assertEqual(loaded.object_list, [])

    def test_manipulation_timestamp_format(self):
        """Verify manipulation_timestamp is in ISO 8601 format."""
        metadata = generate_stimulus_metadata(
            image_id="test_iso",
            image_path="test.jpg",
            object_list=["test"],
            complexity_score=0.5
        )
        
        ts = metadata.manipulation_timestamp
        # ISO 8601 format: YYYY-MM-DDTHH:MM:SS.ffffff
        self.assertRegex(ts, r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', "Timestamp not ISO 8601")