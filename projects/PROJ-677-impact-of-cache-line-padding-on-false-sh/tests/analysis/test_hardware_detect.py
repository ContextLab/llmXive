import os
import sys
import tempfile
from pathlib import Path
import yaml

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis.hardware_detect import (
    get_core_count,
    get_cache_line_size,
    set_cpu_governor,
    generate_hardware_spec
)

def test_get_core_count():
    """Test that core count is a positive integer."""
    count = get_core_count()
    assert isinstance(count, int), "Core count should be an integer"
    assert count > 0, "Core count should be positive"

def test_get_cache_line_size():
    """Test that cache line size is a positive integer, typically 64."""
    size = get_cache_line_size()
    assert isinstance(size, int), "Cache line size should be an integer"
    assert size > 0, "Cache line size should be positive"
    # Most modern CPUs have 64 byte cache lines
    assert size in [32, 64, 128], f"Unexpected cache line size: {size}"

def test_set_cpu_governor():
    """Test that the function returns a boolean indicating success."""
    # Note: This might fail in containers without root/sudo, but should return False
    result = set_cpu_governor('performance')
    assert isinstance(result, bool), "Set governor should return a boolean"

def test_generate_hardware_spec(tmp_path):
    """Test that generate_hardware_spec creates a valid YAML file."""
    output_file = tmp_path / "test_spec.yaml"
    
    spec = generate_hardware_spec(output_file)
    
    # Check file existence
    assert output_file.exists(), "Output file should be created"
    
    # Check content validity
    with open(output_file, 'r') as f:
        loaded_spec = yaml.safe_load(f)
    
    assert 'core_count' in loaded_spec
    assert 'cache_line_size_bytes' in loaded_spec
    assert 'governor_set_to_performance' in loaded_spec
    assert loaded_spec['core_count'] == spec['core_count']
    assert loaded_spec['cache_line_size_bytes'] == spec['cache_line_size_bytes']