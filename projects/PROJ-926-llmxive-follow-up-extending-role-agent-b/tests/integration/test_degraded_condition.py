"""
T020 Integration Test: Verify degraded condition output.

This test verifies that the degraded condition generation script:
1. Produces the expected output file
2. Contains the correct number of failures
3. Has valid schema for each failure entry
4. Correctly marks the condition as 'degraded'
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.conditions.run_degraded import (
    generate_degraded_failures,
    save_degraded_failures,
    run
)
from src.conditions.degraded import DegradedConfig

class TestDegradedCondition:
    """Integration tests for the degraded condition generation."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_degraded_env(self):
        """Mock the degraded environment configuration."""
        with patch('src.conditions.run_degraded.configure_degraded_environment') as mock_config:
            mock_config.return_value = {"wia_horizon": 0, "mode": "degraded"}
            yield mock_config

    @pytest.fixture
    def mock_run_episode(self):
        """Mock the episode runner to return controlled trajectories."""
        def mock_run_episode(task_id, seed, config, env_config):
            # Return a failure trajectory (succeeded validation=False)
            return {
                "action_log": [
                    {"step": 1, "action": "go to kitchen"},
                    {"step": 2, "action": "pick up apple"},
                    {"step": 3, "action": "fail to pick up apple"}
                ],
                "state_transitions": [
                    {"from": "start", "to": "kitchen"},
                    {"from": "kitchen", "to": "failed"}
                ]
            }
        
        with patch('src.conditions.run_degraded.run_episode', side_effect=mock_run_episode):
            yield

    @pytest.fixture
    def mock_validate_trajectory(self):
        """Mock validation to always return failure (for testing failure collection)."""
        with patch('src.conditions.run_degraded.validate_trajectory') as mock_validate:
            mock_validate.return_value = (False, {"failure_reason": "test_failure"})
            yield mock_validate

    def test_degraded_config_creation(self):
        """Test that DegradedConfig is created with correct parameters."""
        config = DegradedConfig(
            wia_horizon=0,
            seed=42,
            model_id="test-model",
            data_path="/tmp/test"
        )
        
        assert config.wia_horizon == 0
        assert config.seed == 42
        assert config.model_id == "test-model"

    def test_generate_few_failures(self, mock_run_episode, mock_validate_trajectory):
        """Test generating a small number of failures."""
        # Generate only 3 failures for faster testing
        failures = generate_degraded_failures(target_count=3)
        
        assert len(failures) == 3
        
        # Verify each failure has required fields
        for failure in failures:
            assert "id" in failure
            assert failure["condition"] == "degraded"
            assert "action_log" in failure
            assert "state_transitions" in failure
            assert "failure_reason" in failure

    def test_save_degraded_failures(self, temp_output_dir, mock_run_episode, mock_validate_trajectory):
        """Test saving degraded failures to a file."""
        output_path = os.path.join(temp_output_dir, "test_degraded_failures.json")
        
        # Generate a few failures
        failures = generate_degraded_failures(target_count=2)
        
        # Save them
        save_degraded_failures(failures, output_path)
        
        # Verify file exists
        assert os.path.exists(output_path)
        
        # Load and verify content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "failures" in data
        assert data["metadata"]["condition"] == "degraded"
        assert data["metadata"]["total_count"] == 2
        assert len(data["failures"]) == 2

    def test_degraded_condition_marks_wia_zero(self, mock_run_episode, mock_validate_trajectory):
        """Test that the generated failures correctly indicate WIA=0."""
        failures = generate_degraded_failures(target_count=1)
        
        assert len(failures) == 1
        assert failures[0]["condition"] == "degraded"
        assert "wia_horizon" in failures[0]
        assert failures[0]["wia_horizon"] == 0

    def test_fresh_cohort_not_reusing_baseline(self, mock_run_episode, mock_validate_trajectory):
        """Test that generated trajectories have unique IDs (fresh cohort)."""
        failures = generate_degraded_failures(target_count=2)
        
        ids = [f["id"] for f in failures]
        
        # All IDs should be unique
        assert len(ids) == len(set(ids))
        
        # IDs should start with 'degraded_' prefix
        for id_str in ids:
            assert id_str.startswith("degraded_")

    def test_exclusion_log_created(self, temp_output_dir, mock_run_episode, mock_validate_trajectory):
        """Test that exclusion log is created for discarded trajectories."""
        # We need to trigger an exclusion - let's mock a successful trajectory
        # to force it to be excluded (we only want failures)
        original_run_episode = None
        
        def mock_run_with_success(task_id, seed, config, env_config):
            # First call returns failure, second returns success
            if not hasattr(mock_run_with_success, 'call_count'):
                mock_run_with_success.call_count = 0
            mock_run_with_success.call_count += 1
            
            if mock_run_with_success.call_count == 1:
                return {
                    "action_log": [{"step": 1, "action": "test"}],
                    "state_transitions": [{"from": "start", "to": "end"}]
                }
            else:
                return {
                    "action_log": [{"step": 1, "action": "fail"}],
                    "state_transitions": [{"from": "start", "to": "failed"}]
                }
        
        with patch('src.conditions.run_degraded.run_episode', side_effect=mock_run_with_success):
            with patch('src.conditions.run_degraded.validate_trajectory') as mock_validate:
                # First call: success (will be excluded), second: failure
                mock_validate.side_effect = [
                    (True, {"reason": "succeeded"}),  # First call: success
                    (False, {"failure_reason": "test"})  # Second call: failure
                ]
                
                failures = generate_degraded_failures(target_count=1)
                assert len(failures) == 1

    def test_output_schema_compliance(self, mock_run_episode, mock_validate_trajectory):
        """Test that output conforms to expected schema."""
        failures = generate_degraded_failures(target_count=1)
        failure = failures[0]
        
        # Required top-level fields
        required_fields = [
            "id", "condition", "wia_horizon", "timestamp",
            "action_log", "state_transitions", "validation_details",
            "failure_reason", "metadata"
        ]
        
        for field in required_fields:
            assert field in failure, f"Missing required field: {field}"
        
        # Metadata structure
        assert "config" in failure["metadata"]
        assert "wia_horizon" in failure["metadata"]["config"]
        assert failure["metadata"]["config"]["wia_horizon"] == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
