"""
Unit tests for configuration management (T006b).
Tests CLI argument parsing and .env support for variance_threshold parameter.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import (
    get_config,
    parse_cli_args,
    load_environment,
    verify_config,
    DEFAULTS
)


class TestConfigParsing:
    """Test configuration parsing from different sources."""

    def test_default_values(self):
        """Test that default configuration values are correct."""
        # Create a mock CLI args object with None values
        mock_args = argparse.Namespace(
            variance_threshold=None,
            seed=None,
            log_level=None,
            output_dir=None,
            project_root=None
        )
        
        config = get_config(mock_args, Path("/tmp"))
        
        assert config["variance_threshold"] == DEFAULTS["variance_threshold"]
        assert config["seed"] == DEFAULTS["seed"]
        assert config["log_level"] == DEFAULTS["log_level"]
        assert config["output_dir"] == DEFAULTS["output_dir"]

    def test_cli_overrides_defaults(self):
        """Test that CLI arguments override default values."""
        mock_args = argparse.Namespace(
            variance_threshold=0.5,
            seed=123,
            log_level="DEBUG",
            output_dir="/custom/output",
            project_root=None
        )
        
        config = get_config(mock_args, Path("/tmp"))
        
        assert config["variance_threshold"] == 0.5
        assert config["seed"] == 123
        assert config["log_level"] == "DEBUG"
        assert config["output_dir"] == "/custom/output"

    def test_env_overrides_defaults(self):
        """Test that .env variables override default values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                "VARIANCE_THRESHOLD=0.75\n"
                "SEED=999\n"
                "LOG_LEVEL=WARNING\n"
            )
            
            mock_args = argparse.Namespace(
                variance_threshold=None,
                seed=None,
                log_level=None,
                output_dir=None,
                project_root=None
            )
            
            config = get_config(mock_args, Path(tmpdir))
            
            assert config["variance_threshold"] == 0.75
            assert config["seed"] == 999
            assert config["log_level"] == "WARNING"

    def test_cli_overrides_env(self):
        """Test that CLI arguments override .env values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                "VARIANCE_THRESHOLD=0.75\n"
                "SEED=999\n"
            )
            
            mock_args = argparse.Namespace(
                variance_threshold=0.25,  # Different from .env
                seed=111,  # Different from .env
                log_level=None,
                output_dir=None,
                project_root=None
            )
            
            config = get_config(mock_args, Path(tmpdir))
            
            # CLI should win
            assert config["variance_threshold"] == 0.25
            assert config["seed"] == 111
            # Log level should come from .env or default
            assert config["log_level"] in ["WARNING", "INFO"]

    def test_variancethreshold_type_conversion(self):
        """Test that variance_threshold is correctly converted to float."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("VARIANCE_THRESHOLD=0.12345\n")
            
            mock_args = argparse.Namespace(
                variance_threshold=None,
                seed=None,
                log_level=None,
                output_dir=None,
                project_root=None
            )
            
            config = get_config(mock_args, Path(tmpdir))
            
            assert isinstance(config["variance_threshold"], float)
            assert abs(config["variance_threshold"] - 0.12345) < 1e-10

    def test_variancethreshold_cli_parsing(self):
        """Test CLI parsing for variance_threshold argument."""
        # Simulate CLI parsing
        sys.argv = ["test", "--variance-threshold", "0.42"]
        args = parse_cli_args()
        
        assert args.variance_threshold == 0.42


class TestConfigValidation:
    """Test configuration validation."""

    def test_valid_config(self):
        """Test that valid configuration passes validation."""
        config = {
            "variance_threshold": 0.1,
            "seed": 42,
            "log_level": "INFO",
            "output_dir": "data/processed"
        }
        
        assert verify_config(config) is True

    def test_invalid_variance_threshold_negative(self):
        """Test that negative variance_threshold fails validation."""
        config = {
            "variance_threshold": -0.1,
            "seed": 42,
            "log_level": "INFO",
            "output_dir": "data/processed"
        }
        
        with pytest.raises(ValueError, match="variance_threshold must be positive"):
            verify_config(config)

    def test_invalid_variance_threshold_zero(self):
        """Test that zero variance_threshold fails validation."""
        config = {
            "variance_threshold": 0.0,
            "seed": 42,
            "log_level": "INFO",
            "output_dir": "data/processed"
        }
        
        with pytest.raises(ValueError, match="variance_threshold must be positive"):
            verify_config(config)

    def test_invalid_seed_negative(self):
        """Test that negative seed fails validation."""
        config = {
            "variance_threshold": 0.1,
            "seed": -1,
            "log_level": "INFO",
            "output_dir": "data/processed"
        }
        
        with pytest.raises(ValueError, match="seed must be non-negative"):
            verify_config(config)

    def test_invalid_log_level(self):
        """Test that invalid log_level fails validation."""
        config = {
            "variance_threshold": 0.1,
            "seed": 42,
            "log_level": "INVALID",
            "output_dir": "data/processed"
        }
        
        with pytest.raises(ValueError, match="log_level must be one of"):
            verify_config(config)


class TestDownstreamIntegration:
    """Test that configuration is correctly read by downstream tasks."""

    def test_config_passed_to_mock_downstream(self):
        """
        Simulate how downstream tasks would use the configuration.
        This verifies the variance_threshold parameter is accessible.
        """
        # Simulate a downstream task that needs variance_threshold
        def mock_downstream_task(config):
            # This is how a downstream task would use the config
            threshold = config["variance_threshold"]
            # Simulate filtering logic
            filtered_count = int(1000 * (1 - threshold))
            return filtered_count
        
        # Test with different thresholds
        for threshold in [0.1, 0.25, 0.5, 0.75]:
            mock_args = argparse.Namespace(
                variance_threshold=threshold,
                seed=None,
                log_level=None,
                output_dir=None,
                project_root=None
            )
            
            config = get_config(mock_args, Path("/tmp"))
            result = mock_downstream_task(config)
            
            expected = int(1000 * (1 - threshold))
            assert result == expected, f"Expected {expected}, got {result}"

    def test_env_var_read_by_downstream(self):
        """Test that downstream tasks can read variance_threshold from .env."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("VARIANCE_THRESHOLD=0.3\n")
            
            mock_args = argparse.Namespace(
                variance_threshold=None,
                seed=None,
                log_level=None,
                output_dir=None,
                project_root=None
            )
            
            config = get_config(mock_args, Path(tmpdir))
            
            # Verify downstream can access it
            assert config["variance_threshold"] == 0.3
            
            # Simulate downstream usage
            def downstream_filter(data, threshold):
                return [x for x in data if x.get("variance", 0) < threshold]
            
            mock_data = [{"variance": 0.1}, {"variance": 0.2}, {"variance": 0.4}]
            filtered = downstream_filter(mock_data, config["variance_threshold"])
            
            assert len(filtered) == 2  # Only items with variance < 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
