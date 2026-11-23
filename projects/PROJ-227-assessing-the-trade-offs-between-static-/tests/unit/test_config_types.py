"""
Unit tests for T004: Configuration Management.
Verifies that config.yaml loads correctly and adheres to the schema.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Add parent directory to path to import verify_config if needed, 
# though we will test the loading logic directly here.
sys.path.insert(0, str(Path(__file__).parent.parent))

CONFIG_PATH = Path(__file__).parent.parent / "code" / "config.yaml"

def test_config_file_exists():
    assert CONFIG_PATH.exists(), "config.yaml must exist"

def test_config_loads_as_dict():
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    assert isinstance(config, dict), "Config must be a dictionary"

def test_schema_types():
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    
    # Check string fields
    assert isinstance(config.get('human_eval_url'), str), "human_eval_url must be a string"
    assert isinstance(config.get('codeql_path'), str), "codeql_path must be a string"
    assert isinstance(config.get('sonar_path'), str), "sonar_path must be a string"
    
    # Check integer fields
    assert isinstance(config.get('max_cpu'), int), "max_cpu must be an int"
    assert isinstance(config.get('max_ram_gb'), int), "max_ram_gb must be an int"

def test_required_keys_present():
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    
    required = ['human_eval_url', 'codeql_path', 'sonar_path', 'max_cpu', 'max_ram_gb']
    for key in required:
        assert key in config, f"Missing required key: {key}"

def test_numeric_constraints_positive():
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    
    assert config['max_cpu'] > 0, "max_cpu must be positive"
    assert config['max_ram_gb'] > 0, "max_ram_gb must be positive"