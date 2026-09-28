import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import pytest
import yaml

# Import the module under test
import sys
sys.path.append(str(Path(__file__).parent.parent / 'code'))

from stimuli.metadata import (
    StimulusMetadata,
    ManipulationRecord,
    generate_metadata_for_image,
    save_metadata_as_yaml,
    load_metadata_from_yaml,
    generate_stimulus_metadata,
    load_generation_log
)

from config import get_stimuli_dir


class TestStimulusMetadataGeneration:
    """Tests for the stimulus metadata generation functionality."""

    def test_generate_baseline_metadata(self, tmp_path):
        """Test generation of baseline metadata."""
        # Mock image ID and path
        image_id = "test_baseline_001"
        image_path = str(tmp_path / f"{image_id}.png")
        
        # Create a dummy file
        Path(tmp_path / f"{image_id}.png").touch()

        # Generate metadata
        meta = generate_metadata_for_image(
            image_id=image_id,
            image_path=image_path,
            manipulation_type='baseline'
        )

        # Assertions
        assert meta.id == image_id
        assert meta.path == image_path
        assert meta.type == 'baseline'
        assert meta.detail_level == 'baseline'
        assert meta.baseline_id is None
        assert meta.manipulation_timestamp is None
        assert meta.manipulation_record is None
        assert meta.version == '1.0'

    def test_generate_enhanced_metadata(self, tmp_path):
        """Test generation of enhanced metadata."""
        image_id = "enhanced_test_001"
        base_id = "test_001"
        image_path = str(tmp_path / f"{image_id}.png")
        
        # Create dummy file
        Path(tmp_path / f"{image_id}.png").touch()

        # Mock generation log entry
        mock_params = {
            "object_name": "cup",
            "shape_type": "circle",
            "x": 120.5,
            "y": 240.1,
            "count": 5
        }

        # Generate metadata
        meta = generate_metadata_for_image(
            image_id=image_id,
            image_path=image_path,
            manipulation_type='enhanced',
            baseline_id=base_id,
            manipulation_params=mock_params
        )

        # Assertions
        assert meta.id == image_id
        assert meta.type == 'enhanced'
        assert meta.detail_level == 'enhanced'
        assert meta.baseline_id == base_id
        assert meta.manipulation_timestamp is not None
        assert meta.manipulation_record is not None
        assert meta.manipulation_record['operation_type'] == 'enhanced'
        assert meta.manipulation_record['parameters']['object_name'] == 'cup'

    def test_generate_reduced_metadata(self, tmp_path):
        """Test generation of reduced metadata."""
        image_id = "reduced_test_001"
        base_id = "test_001"
        image_path = str(tmp_path / f"{image_id}.png")
        
        # Create dummy file
        Path(tmp_path / f"{image_id}.png").touch()

        # Mock generation log entry
        mock_params = {
            "object_name": "removed_obj",
            "count": 3
        }

        # Generate metadata
        meta = generate_metadata_for_image(
            image_id=image_id,
            image_path=image_path,
            manipulation_type='reduced',
            baseline_id=base_id,
            manipulation_params=mock_params
        )

        # Assertions
        assert meta.id == image_id
        assert meta.type == 'reduced'
        assert meta.detail_level == 'reduced'
        assert meta.baseline_id == base_id
        assert meta.manipulation_record is not None
        assert meta.manipulation_record['operation_type'] == 'reduced'

    def test_save_and_load_metadata_yaml(self, tmp_path):
        """Test saving and loading metadata from YAML."""
        # Create a metadata object
        meta = generate_metadata_for_image(
            image_id="test_yaml_001",
            image_path=str(tmp_path / "test_yaml_001.png"),
            manipulation_type='baseline'
        )

        # Save to YAML
        output_path = str(tmp_path / "test_metadata.yaml")
        save_metadata_as_yaml(meta, output_path)

        # Verify file exists
        assert os.path.exists(output_path)

        # Load back
        loaded_meta = load_metadata_from_yaml(output_path)

        # Verify content
        assert loaded_meta.id == meta.id
        assert loaded_meta.type == meta.type
        assert loaded_meta.path == meta.path

    def test_generate_stimulus_metadata_batch(self, tmp_path):
        """Test batch generation of metadata for multiple stimuli."""
        # Setup test files
        baseline_ids = ["base_001", "base_002"]
        enhanced_ids = ["enhanced_base_001", "enhanced_base_002"]
        reduced_ids = ["reduced_base_001", "reduced_base_002"]

        # Create dummy image files
        for img_id in baseline_ids + enhanced_ids + reduced_ids:
            Path(tmp_path / f"{img_id}.png").touch()

        # Mock generation log
        gen_log_path = tmp_path / "generation_log.json"
        with open(gen_log_path, 'w') as f:
            json.dump([{"object_name": "test_obj", "count": 1}], f)

        # Run batch generation
        output_map = generate_stimulus_metadata(
            baseline_ids=baseline_ids,
            enhanced_ids=enhanced_ids,
            reduced_ids=reduced_ids,
            generation_log_path=str(gen_log_path)
        )

        # Verify all metadata files were created
        assert len(output_map) == len(baseline_ids) + len(enhanced_ids) + len(reduced_ids)

        # Verify file existence
        for img_id, file_path in output_map.items():
            assert os.path.exists(file_path), f"Metadata file missing for {img_id}: {file_path}"
            # Verify it's valid YAML
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
                assert 'id' in data
                assert 'type' in data

    def test_metadata_contains_timestamp(self, tmp_path):
        """Verify that generated metadata contains valid timestamps."""
        meta = generate_metadata_for_image(
            image_id="time_test",
            image_path=str(tmp_path / "time_test.png"),
            manipulation_type='enhanced'
        )

        # Check created_at is ISO format
        assert meta.created_at is not None
        datetime.fromisoformat(meta.created_at.replace('Z', '+00:00'))

        # Check manipulation_timestamp is ISO format for non-baseline
        assert meta.manipulation_timestamp is not None
        datetime.fromisoformat(meta.manipulation_timestamp.replace('Z', '+00:00'))

    def test_metadata_file_naming_convention(self, tmp_path):
        """Verify that metadata files follow the expected naming convention."""
        # Create dummy images
        test_ids = ["base_001", "enhanced_base_001", "reduced_base_001"]
        for img_id in test_ids:
            Path(tmp_path / f"{img_id}.png").touch()

        gen_log_path = tmp_path / "gen_log.json"
        with open(gen_log_path, 'w') as f:
            json.dump([{"object": "test"}], f)

        output_map = generate_stimulus_metadata(
            baseline_ids=["base_001"],
            enhanced_ids=["enhanced_base_001"],
            reduced_ids=["reduced_base_001"],
            generation_log_path=str(gen_log_path)
        )

        # Check filenames
        assert output_map["base_001"].endswith("base_001_metadata.yaml")
        assert output_map["enhanced_base_001"].endswith("enhanced_enhanced_base_001_metadata.yaml")
        assert output_map["reduced_base_001"].endswith("reduced_reduced_base_001_metadata.yaml")
