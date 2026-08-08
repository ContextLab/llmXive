import pytest
import os
from pathlib import Path
import sys

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import (
    get_dataset_ids, 
    get_sample_limit, 
    get_config_summary, 
    validate_config,
    PRIMARY_DATASET_ID,
    FALLBACK_DATASET_ID,
    CI_SAMPLE_LIMIT,
    MAX_SUBJECTS
)

class TestConfig:
    def test_get_dataset_ids_returns_tuple(self):
        """Test that get_dataset_ids returns a tuple of two strings."""
        result = get_dataset_ids()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)

    def test_primary_dataset_is_ds000224(self):
        """Verify primary dataset is ds000224 as per T008b."""
        primary, fallback = get_dataset_ids()
        assert primary == "ds000224"

    def test_fallback_dataset_is_ds000230(self):
        """Verify fallback dataset is ds000230 as per T008b."""
        primary, fallback = get_dataset_ids()
        assert fallback == "ds000230"

    def test_sample_limit_defaults_to_max(self):
        """Test that sample limit defaults to MAX_SUBJECTS (50) when not in CI."""
        # Ensure CI is not set
        original_ci = os.environ.get("CI")
        if "CI" in os.environ:
            del os.environ["CI"]
        
        limit = get_sample_limit()
        assert limit == MAX_SUBJECTS
        
        # Restore
        if original_ci is not None:
            os.environ["CI"] = original_ci

    def test_sample_limit_is_10_in_ci(self):
        """Test that sample limit is 10 when in CI mode as per T008b."""
        os.environ["CI"] = "true"
        limit = get_sample_limit()
        assert limit == 10
        del os.environ["CI"]

    def test_config_summary_contains_keys(self):
        """Test that config summary contains required keys."""
        summary = get_config_summary()
        assert "primary_dataset" in summary
        assert "fallback_dataset" in summary
        assert "ci_limit" in summary
        assert "max_subjects" in summary
        assert "current_limit" in summary

    def test_config_summary_values(self):
        """Test that config summary values are correct."""
        summary = get_config_summary()
        assert summary["primary_dataset"] == "ds000224"
        assert summary["fallback_dataset"] == "ds000230"
        assert summary["ci_limit"] == 10
        assert summary["max_subjects"] == 50

    def test_validate_config_returns_true(self):
        """Test that validate_config returns True for valid config."""
        assert validate_config() is True

    def test_yaml_file_exists(self):
        """Verify that config.yaml exists in the project root."""
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / "config.yaml"
        assert config_file.exists(), "config.yaml must exist in project root"

    def test_yaml_file_contains_required_ids(self):
        """Verify config.yaml contains the correct dataset IDs."""
        import yaml
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / "config.yaml"
        
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data["datasets"]["primary"]["id"] == "ds000224"
        assert data["datasets"]["fallback"]["id"] == "ds000230"
        assert data["datasets"]["fallback"]["usage_constraint"] == "fallback_only"
        assert data["sampling"]["ci_limit"] == 10