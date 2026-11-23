"""
Integration test to verify the config.yaml file matches the T010 specification exactly.
This test ensures the file is syntactically correct and contains the specific keys
mandated by the task description.
"""
import pytest
import yaml
from pathlib import Path

# Path relative to project root
CONFIG_FILE = Path(__file__).parent.parent.parent / "config.yaml"

@pytest.fixture
def config_data():
    if not CONFIG_FILE.exists():
        pytest.fail("config.yaml does not exist")
    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)

def test_yaml_syntax_is_valid(config_data):
    """Task T010 Verification: Verify YAML syntax."""
    # If we got here via the fixture, the load was successful.
    # This test exists to make the check explicit in the report.
    assert isinstance(config_data, dict), "Root must be a dictionary"

def test_primary_dataset_key_exists(config_data):
    """Task T010 Verification: Presence of primary dataset key."""
    assert "datasets" in config_data, "Missing 'datasets' section"
    assert "primary" in config_data["datasets"], "Missing 'datasets.primary' key"

def test_fallback_dataset_key_exists(config_data):
    """Task T010 Verification: Presence of fallback_only dataset key."""
    assert "datasets" in config_data, "Missing 'datasets' section"
    assert "fallback_only" in config_data["datasets"], "Missing 'datasets.fallback_only' key"

def test_sample_limit_key_exists(config_data):
    """Task T010 Verification: Presence of sample limit key."""
    assert "sample_limit" in config_data, "Missing 'sample_limit' key"

def test_primary_value_is_ds000224(config_data):
    """Task T010 Verification: Primary dataset is ds000224."""
    assert config_data["datasets"]["primary"] == "ds000224", \
        f"Expected 'ds000224', got '{config_data['datasets']['primary']}'"

def test_fallback_value_is_ds000230(config_data):
    """Task T010 Verification: Fallback dataset is ds000230."""
    assert config_data["datasets"]["fallback_only"] == "ds000230", \
        f"Expected 'ds000230', got '{config_data['datasets']['fallback_only']}'"

def test_sample_limit_value_is_10(config_data):
    """Task T010 Verification: N=10 sample limit."""
    assert config_data["sample_limit"] == 10, \
        f"Expected 10, got {config_data['sample_limit']}"
    assert isinstance(config_data["sample_limit"], int), \
        "sample_limit must be an integer"

def test_no_unexpected_top_level_keys(config_data):
    """Ensure no unexpected top-level keys were added."""
    expected_keys = {"datasets", "sample_limit", "processing"}
    actual_keys = set(config_data.keys())
    # Allow 'processing' as it is standard for the project, but warn if others exist
    unexpected = actual_keys - expected_keys
    assert len(unexpected) == 0, f"Unexpected top-level keys found: {unexpected}"
