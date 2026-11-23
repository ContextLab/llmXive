"""
Unit tests for T004: Configuration Management.
Verifies that config.yaml loads correctly and types are valid.
"""
import pytest
import yaml
from pathlib import Path
import sys

# Add parent code directory to path for imports if needed, 
# though this test primarily validates the file content directly.
project_root = Path(__file__).parent.parent.parent
config_path = project_root / "code" / "config.yaml"

@pytest.fixture
def config_data():
    if not config_path.exists():
        pytest.skip(f"Config file not found at {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def test_config_exists():
    assert config_path.exists(), "config.yaml must exist"

def test_config_is_dict(config_data):
    assert isinstance(config_data, dict), "Config must be a dictionary"

def test_human_eval_url_type(config_data):
    assert isinstance(config_data.get("human_eval_url"), str), "human_eval_url must be a string"

def test_codeql_path_type(config_data):
    assert isinstance(config_data.get("codeql_path"), str), "codeql_path must be a string"

def test_sonar_path_type(config_data):
    assert isinstance(config_data.get("sonar_path"), str), "sonar_path must be a string"

def test_max_cpu_type(config_data):
    val = config_data.get("max_cpu")
    assert isinstance(val, int) and not isinstance(val, bool), "max_cpu must be an integer"
    assert val > 0, "max_cpu must be positive"

def test_max_ram_gb_type(config_data):
    val = config_data.get("max_ram_gb")
    assert isinstance(val, int) and not isinstance(val, bool), "max_ram_gb must be an integer"
    assert val > 0, "max_ram_gb must be positive"

def test_required_keys_present(config_data):
    required = ["human_eval_url", "codeql_path", "sonar_path", "max_cpu", "max_ram_gb"]
    for key in required:
        assert key in config_data, f"Missing required key: {key}"