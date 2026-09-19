"""
Unit tests for the checkpoint manager functionality.
"""
import os
import json
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import hashlib

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from checkpoint_manager import (
    ensure_checkpoint_dir,
    generate_scenario_id,
    save_checkpoint,
    load_latest_checkpoint,
    should_save_checkpoint,
    get_resume_scenario_ids,
    update_manifest,
    CHECKPOINT_INTERVAL
)


class TestCheckpointManager:
    """Test cases for checkpoint manager functions."""

    @pytest.fixture
    def temp_checkpoint_dir(self):
        """Create a temporary directory for checkpoint tests."""
        temp_dir = tempfile.mkdtemp()
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        
        # Patch the CHECKPOINT_DIR constant
        with patch('checkpoint_manager.CHECKPOINT_DIR', temp_dir):
            yield temp_dir
        
        os.chdir(original_dir)
        shutil.rmtree(temp_dir)

    def test_ensure_checkpoint_dir_creates_directory(self, temp_checkpoint_dir):
        """Test that ensure_checkpoint_dir creates the directory if it doesn't exist."""
        result = ensure_checkpoint_dir()
        assert os.path.isdir(result)
        assert result == temp_checkpoint_dir

    def test_generate_scenario_id_deterministic(self):
        """Test that scenario ID generation is deterministic."""
        config1 = {"n": 100, "dist": "normal", "test": "t-test"}
        config2 = {"n": 100, "dist": "normal", "test": "t-test"}
        config3 = {"n": 200, "dist": "normal", "test": "t-test"}
        
        id1 = generate_scenario_id(config1)
        id2 = generate_scenario_id(config2)
        id3 = generate_scenario_id(config3)
        
        assert id1 == id2  # Same config -> same ID
        assert id1 != id3  # Different config -> different ID
        assert len(id1) == 12  # Truncated hash length

    def test_should_save_checkpoint_at_interval(self):
        """Test checkpoint saving logic at regular intervals."""
        # Should save at multiples of CHECKPOINT_INTERVAL
        assert should_save_checkpoint(CHECKPOINT_INTERVAL) is True
        assert should_save_checkpoint(CHECKPOINT_INTERVAL * 2) is True
        assert should_save_checkpoint(CHECKPOINT_INTERVAL * 10) is True
        
        # Should not save at non-multiples
        assert should_save_checkpoint(CHECKPOINT_INTERVAL - 1) is False
        assert should_save_checkpoint(1) is False
        assert should_save_checkpoint(0) is False

    def test_save_checkpoint_creates_file(self, temp_checkpoint_dir):
        """Test that save_checkpoint creates a valid checkpoint file."""
        scenario_id = "test_scenario_123"
        config = {"n": 100, "dist": "normal"}
        results = [{"p_value": 0.05, "replicate": 1}]
        
        checkpoint_path = save_checkpoint(
            scenario_id=scenario_id,
            current_replicate=100,
            results=results,
            config=config,
            status="running"
        )
        
        assert os.path.exists(checkpoint_path)
        assert checkpoint_path.endswith(".pkl")
        
        # Verify manifest was updated
        manifest_path = os.path.join(temp_checkpoint_dir, "checkpoint_manifest.json")
        assert os.path.exists(manifest_path)
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert len(manifest["checkpoints"]) == 1
        assert manifest["checkpoints"][0]["scenario_id"] == scenario_id
        assert manifest["checkpoints"][0]["current_replicate"] == 100
        assert manifest["checkpoints"][0]["status"] == "running"

    def test_load_latest_checkpoint_success(self, temp_checkpoint_dir):
        """Test loading the latest checkpoint."""
        scenario_id = "test_scenario_456"
        config = {"n": 200, "dist": "uniform"}
        results = [{"p_value": 0.03, "replicate": i} for i in range(1, 201)]
        
        # Save a checkpoint
        save_checkpoint(
            scenario_id=scenario_id,
            current_replicate=200,
            results=results,
            config=config,
            status="running"
        )
        
        # Load it back
        loaded_data = load_latest_checkpoint(scenario_id)
        
        assert loaded_data is not None
        assert loaded_data["scenario_id"] == scenario_id
        assert loaded_data["current_replicate"] == 200
        assert len(loaded_data["results"]) == 200
        assert loaded_data["status"] == "running"
        assert loaded_data["config"] == config

    def test_load_latest_checkpoint_not_found(self, temp_checkpoint_dir):
        """Test loading a checkpoint that doesn't exist."""
        result = load_latest_checkpoint("non_existent_scenario")
        assert result is None

    def test_load_latest_checkpoint_checksum_mismatch(self, temp_checkpoint_dir):
        """Test handling of checksum mismatch."""
        scenario_id = "test_scenario_789"
        config = {"n": 50}
        results = [{"p_value": 0.01}]
        
        # Save checkpoint
        save_checkpoint(
            scenario_id=scenario_id,
            current_replicate=50,
            results=results,
            config=config,
            status="running"
        )
        
        # Corrupt the results in the checkpoint file
        manifest_path = os.path.join(temp_checkpoint_dir, "checkpoint_manifest.json")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        checkpoint_file = manifest["checkpoints"][0]["checkpoint_file"]
        checkpoint_path = os.path.join(temp_checkpoint_dir, checkpoint_file)
        
        # We can't easily corrupt the pickle without breaking it,
        # so we'll test the checksum logic by mocking
        with patch('checkpoint_manager.hashlib.md5') as mock_md5:
            mock_md5.return_value.hexdigest.return_value = "wrong_checksum"
            result = load_latest_checkpoint(scenario_id)
            assert result is None  # Should fail due to checksum mismatch

    def test_get_resume_scenario_ids(self, temp_checkpoint_dir):
        """Test getting list of scenarios with active checkpoints."""
        # Save checkpoints for multiple scenarios
        save_checkpoint("scenario_a", 100, [], {"n": 10}, "running")
        save_checkpoint("scenario_b", 200, [], {"n": 20}, "completed")
        save_checkpoint("scenario_c", 300, [], {"n": 30}, "running")
        
        running = get_resume_scenario_ids()
        
        assert len(running) == 2
        assert "scenario_a" in running
        assert "scenario_c" in running
        assert "scenario_b" not in running  # Completed, not running

    def test_update_manifest_adds_new_entry(self, temp_checkpoint_dir):
        """Test that update_manifest adds a new entry correctly."""
        checkpoint_path = os.path.join(temp_checkpoint_dir, "test.pkl")
        
        # Create a dummy file
        Path(checkpoint_path).touch()
        
        update_manifest(checkpoint_path, "new_scenario", 150, "running")
        
        manifest_path = os.path.join(temp_checkpoint_dir, "checkpoint_manifest.json")
        assert os.path.exists(manifest_path)
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert len(manifest["checkpoints"]) == 1
        assert manifest["checkpoints"][0]["scenario_id"] == "new_scenario"

    def test_update_manifest_replaces_existing_entry(self, temp_checkpoint_dir):
        """Test that update_manifest replaces existing entry for same scenario."""
        checkpoint_path = os.path.join(temp_checkpoint_dir, "test.pkl")
        Path(checkpoint_path).touch()
        
        # Add initial entry
        update_manifest(checkpoint_path, "existing_scenario", 100, "running")
        
        # Update with new data
        new_path = os.path.join(temp_checkpoint_dir, "test2.pkl")
        Path(new_path).touch()
        update_manifest(new_path, "existing_scenario", 200, "completed")
        
        manifest_path = os.path.join(temp_checkpoint_dir, "checkpoint_manifest.json")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Should have only one entry for the scenario
        scenario_entries = [
            cp for cp in manifest["checkpoints"]
            if cp["scenario_id"] == "existing_scenario"
        ]
        assert len(scenario_entries) == 1
        assert scenario_entries[0]["current_replicate"] == 200
        assert scenario_entries[0]["status"] == "completed"

    def test_save_checkpoint_with_empty_results(self, temp_checkpoint_dir):
        """Test saving a checkpoint with empty results list."""
        scenario_id = "empty_results_scenario"
        config = {"n": 10}
        
        checkpoint_path = save_checkpoint(
            scenario_id=scenario_id,
            current_replicate=0,
            results=[],
            config=config,
            status="running"
        )
        
        assert os.path.exists(checkpoint_path)
        
        # Load and verify
        loaded = load_latest_checkpoint(scenario_id)
        assert loaded is not None
        assert len(loaded["results"]) == 0
        assert loaded["current_replicate"] == 0

    def test_save_checkpoint_with_large_results(self, temp_checkpoint_dir):
        """Test saving a checkpoint with a large number of results."""
        scenario_id = "large_results_scenario"
        config = {"n": 1000}
        results = [{"p_value": i / 10000, "replicate": i} for i in range(1000)]
        
        checkpoint_path = save_checkpoint(
            scenario_id=scenario_id,
            current_replicate=1000,
            results=results,
            config=config,
            status="running"
        )
        
        assert os.path.exists(checkpoint_path)
        
        loaded = load_latest_checkpoint(scenario_id)
        assert loaded is not None
        assert len(loaded["results"]) == 1000
        assert loaded["current_replicate"] == 1000
        assert loaded["config"] == config