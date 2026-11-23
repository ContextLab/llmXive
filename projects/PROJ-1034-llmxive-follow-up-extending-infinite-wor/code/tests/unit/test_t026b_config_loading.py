import pytest
import os
import tempfile
import yaml
import sys
from pathlib import Path

# Add code to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.cli.run_simulation import load_target_steps_from_config, verify_step_count

class TestT026bConfigLoading:
    """
    Unit tests for T026b: Configuration loading logic.
    Verifies that target_steps is read from config.yaml correctly.
    """

    def test_load_target_steps_from_valid_config(self):
        """Test loading target_steps from a valid config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"target_steps": 5000}, f)
            config_path = f.name

        try:
            steps = load_target_steps_from_config(config_path)
            assert steps == 5000, f"Expected 5000, got {steps}"
        finally:
            os.unlink(config_path)

    def test_load_target_steps_from_missing_config(self):
        """Test that missing config file returns default and logs warning."""
        steps = load_target_steps_from_config("/nonexistent/path/config.yaml")
        assert steps == 1000, f"Expected default 1000, got {steps}"

    def test_load_target_steps_from_empty_config(self):
        """Test loading from an empty config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            config_path = f.name

        try:
            steps = load_target_steps_from_config(config_path)
            assert steps == 1000, f"Expected default 1000, got {steps}"
        finally:
            os.unlink(config_path)

    def test_load_target_steps_missing_key(self):
        """Test config file without target_steps key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"other_key": "value"}, f)
            config_path = f.name

        try:
            steps = load_target_steps_from_config(config_path)
            assert steps == 1000, f"Expected default 1000, got {steps}"
        finally:
            os.unlink(config_path)

    def test_load_target_steps_invalid_value(self):
        """Test config with invalid target_steps value."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"target_steps": "invalid"}, f)
            config_path = f.name

        try:
            steps = load_target_steps_from_config(config_path)
            assert steps == 1000, f"Expected default 1000, got {steps}"
        finally:
            os.unlink(config_path)

    def test_verify_step_count_pass(self):
        """Test verify_step_count when actual >= target."""
        assert verify_step_count(1000, 1000) is True
        assert verify_step_count(1500, 1000) is True

    def test_verify_step_count_fail(self):
        """Test verify_step_count when actual < target."""
        assert verify_step_count(999, 1000) is False
        assert verify_step_count(500, 1000) is False
