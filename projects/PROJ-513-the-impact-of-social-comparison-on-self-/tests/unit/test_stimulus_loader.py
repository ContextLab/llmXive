"""
Unit tests for stimulus sequence generation and matching logic.

This module implements contract tests for the stimulus_loader module,
specifically verifying:
1. Correct loading of metadata for AI and Human stimuli.
2. Validation of required metadata fields (pose, lighting, etc.).
3. Correct pairing of AI and Human stimuli based on metadata matching.
4. Proper error handling for missing or invalid metadata.

These tests verify the core contract required for randomized presentation
in the data collection interface (T013).
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from code.stimulus_loader import (
    get_stimuli_paths,
    load_metadata,
    validate_metadata_fields,
    get_matched_pairs,
    StimulusLoadError,
    MetadataValidationError
)


class TestGetStimuliPaths:
    """Tests for the get_stimuli_paths function."""

    def test_returns_valid_paths_for_ai_and_human(self, tmp_path):
        """Test that the function returns valid paths for both AI and Human directories."""
        # Setup: Create directory structure
        ai_dir = tmp_path / "data" / "stimuli" / "ai"
        human_dir = tmp_path / "data" / "stimuli" / "human"
        ai_dir.mkdir(parents=True)
        human_dir.mkdir(parents=True)

        # Create dummy metadata files
        (ai_dir / "img_001.json").write_text('{"id": "img_001"}')
        (human_dir / "img_002.json").write_text('{"id": "img_002"}')

        # Execute
        ai_paths, human_paths = get_stimuli_paths(tmp_path / "data" / "stimuli")

        # Assert
        assert len(ai_paths) == 1
        assert len(human_paths) == 1
        assert ai_paths[0].name == "img_001.json"
        assert human_paths[0].name == "img_002.json"

    def test_raises_error_when_directory_missing(self, tmp_path):
        """Test that the function raises an error when the stimuli directory is missing."""
        # Setup
        stimuli_dir = tmp_path / "data" / "stimuli"

        # Execute and Assert
        with pytest.raises(StimulusLoadError, match="Stimuli directory not found"):
            get_stimuli_paths(stimuli_dir)

    def test_returns_empty_lists_when_no_metadata(self, tmp_path):
        """Test that empty lists are returned when no metadata files exist."""
        # Setup
        ai_dir = tmp_path / "data" / "stimuli" / "ai"
        human_dir = tmp_path / "data" / "stimuli" / "human"
        ai_dir.mkdir(parents=True)
        human_dir.mkdir(parents=True)

        # Execute
        ai_paths, human_paths = get_stimuli_paths(tmp_path / "data" / "stimuli")

        # Assert
        assert len(ai_paths) == 0
        assert len(human_paths) == 0


class TestLoadMetadata:
    """Tests for the load_metadata function."""

    def test_loads_valid_json(self, tmp_path):
        """Test that valid JSON metadata is loaded correctly."""
        # Setup
        metadata_path = tmp_path / "test.json"
        expected_data = {"id": "test_001", "pose": "standing", "lighting": "bright"}
        metadata_path.write_text(json.dumps(expected_data))

        # Execute
        result = load_metadata(metadata_path)

        # Assert
        assert result == expected_data

    def test_raises_error_on_invalid_json(self, tmp_path):
        """Test that an error is raised for invalid JSON content."""
        # Setup
        metadata_path = tmp_path / "test.json"
        metadata_path.write_text("not valid json {")

        # Execute and Assert
        with pytest.raises(StimulusLoadError, match="Failed to parse JSON"):
            load_metadata(metadata_path)

    def test_raises_error_on_missing_file(self, tmp_path):
        """Test that an error is raised when the file does not exist."""
        # Setup
        metadata_path = tmp_path / "nonexistent.json"

        # Execute and Assert
        with pytest.raises(StimulusLoadError, match="Metadata file not found"):
            load_metadata(metadata_path)


class TestValidateMetadataFields:
    """Tests for the validate_metadata_fields function."""

    def test_passes_with_required_fields(self):
        """Test validation passes when all required fields are present."""
        # Setup
        metadata = {
            "id": "img_001",
            "pose": "standing",
            "lighting": "bright",
            "origin": "AI"
        }
        required_fields = ["id", "pose", "lighting"]

        # Execute
        result = validate_metadata_fields(metadata, required_fields)

        # Assert
        assert result is True

    def test_fails_with_missing_field(self):
        """Test validation fails when a required field is missing."""
        # Setup
        metadata = {
            "id": "img_001",
            "lighting": "bright"
            # missing 'pose'
        }
        required_fields = ["id", "pose", "lighting"]

        # Execute and Assert
        with pytest.raises(MetadataValidationError, match="Missing required field: pose"):
            validate_metadata_fields(metadata, required_fields)

    def test_fails_with_empty_metadata(self):
        """Test validation fails when metadata is empty."""
        # Setup
        metadata = {}
        required_fields = ["id", "pose"]

        # Execute and Assert
        with pytest.raises(MetadataValidationError, match="Missing required field: id"):
            validate_metadata_fields(metadata, required_fields)


class TestGetMatchedPairs:
    """Tests for the get_matched_pairs function which is critical for randomization."""

    def test_matches_by_pose_and_lighting(self, tmp_path):
        """Test that pairs are correctly matched based on pose and lighting."""
        # Setup
        ai_dir = tmp_path / "data" / "stimuli" / "ai"
        human_dir = tmp_path / "data" / "stimuli" / "human"
        ai_dir.mkdir(parents=True)
        human_dir.mkdir(parents=True)

        # Create AI metadata
        ai_data = [
            {"id": "ai_1", "pose": "standing", "lighting": "bright"},
            {"id": "ai_2", "pose": "sitting", "lighting": "dim"}
        ]
        # Create Human metadata (matching)
        human_data = [
            {"id": "human_1", "pose": "standing", "lighting": "bright"},
            {"id": "human_2", "pose": "sitting", "lighting": "dim"}
        ]

        for i, data in enumerate(ai_data):
            (ai_dir / f"ai_{i+1}.json").write_text(json.dumps(data))
        for i, data in enumerate(human_data):
            (human_dir / f"human_{i+1}.json").write_text(json.dumps(data))

        # Execute
        pairs = get_matched_pairs(tmp_path / "data" / "stimuli")

        # Assert
        assert len(pairs) == 2
        # Check that pairs contain the correct IDs
        ai_ids = {p[0]["id"] for p in pairs}
        human_ids = {p[1]["id"] for p in pairs}
        assert ai_ids == {"ai_1", "ai_2"}
        assert human_ids == {"human_1", "human_2"}

    def test_raises_error_on_unmatched_stimuli(self, tmp_path):
        """Test that an error is raised if a stimulus has no match."""
        # Setup
        ai_dir = tmp_path / "data" / "stimuli" / "ai"
        human_dir = tmp_path / "data" / "stimuli" / "human"
        ai_dir.mkdir(parents=True)
        human_dir.mkdir(parents=True)

        # AI has a standing pose
        (ai_dir / "ai_1.json").write_text(json.dumps({"id": "ai_1", "pose": "standing", "lighting": "bright"}))
        # Human only has sitting (no match for standing)
        (human_dir / "human_1.json").write_text(json.dumps({"id": "human_1", "pose": "sitting", "lighting": "dim"}))

        # Execute and Assert
        with pytest.raises(StimulusLoadError, match="No matching human stimulus found"):
            get_matched_pairs(tmp_path / "data" / "stimuli")

    def test_handles_multiple_matches_correctly(self, tmp_path):
        """Test behavior when multiple human stimuli match one AI stimulus."""
        # Setup
        ai_dir = tmp_path / "data" / "stimuli" / "ai"
        human_dir = tmp_path / "data" / "stimuli" / "human"
        ai_dir.mkdir(parents=True)
        human_dir.mkdir(parents=True)

        # One AI standing
        (ai_dir / "ai_1.json").write_text(json.dumps({"id": "ai_1", "pose": "standing", "lighting": "bright"}))
        # Two Humans standing
        (human_dir / "human_1.json").write_text(json.dumps({"id": "human_1", "pose": "standing", "lighting": "bright"}))
        (human_dir / "human_2.json").write_text(json.dumps({"id": "human_2", "pose": "standing", "lighting": "bright"}))

        # Execute
        pairs = get_matched_pairs(tmp_path / "data" / "stimuli")

        # Assert: Should pair the AI with the first match found (or all, depending on implementation)
        # Assuming implementation picks one match per AI for the experiment
        assert len(pairs) == 1
        assert pairs[0][0]["id"] == "ai_1"
        # The human ID should be one of the standing ones
        assert pairs[0][1]["id"] in ["human_1", "human_2"]