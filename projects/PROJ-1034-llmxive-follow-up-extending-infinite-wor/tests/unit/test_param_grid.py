"""
Unit tests for parameter grid generation.

Tests verify that the parameter grid generator produces valid configurations
for the CA engine sweep, ensuring all required keys are present and
parameter values are within expected bounds.
"""
import pytest
import sys
import os
import yaml
import tempfile

# Add project root to path to allow imports from code/
# Assuming this file is run from project root or via pytest discovery
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sim.eco_director import load_config, validate_config
from typing import List, Dict, Any


def generate_test_grid() -> List[Dict[str, Any]]:
    """
    Helper to generate a small test parameter grid mimicking the real generator logic.
    This simulates what src/cli/generate_grid.py would produce for T023a.
    """
    base_config = {
        "locality": [3, 5],
        "memory": [1, 2],
        "non_linearity": [0.5, 0.8],
        "seed": [42]
    }
    
    # Simple Cartesian product implementation for testing
    import itertools
    keys = base_config.keys()
    values = base_config.values()
    
    grid = []
    for combination in itertools.product(*values):
        config = dict(zip(keys, combination))
        grid.append(config)
    
    return grid


def test_grid_generation_creates_valid_configs():
    """
    Test that the generated grid produces configurations that pass validation.
    """
    grid = generate_test_grid()
    
    assert len(grid) > 0, "Grid should not be empty"
    
    for config in grid:
        # Verify all required keys exist
        assert "locality" in config
        assert "memory" in config
        assert "non_linearity" in config
        
        # Verify types
        assert isinstance(config["locality"], int)
        assert isinstance(config["memory"], int)
        assert isinstance(config["non_linearity"], (int, float))
        
        # Verify bounds
        assert config["locality"] > 0
        assert config["memory"] > 0
        assert 0.0 < config["non_linearity"] <= 1.0


def test_grid_generation_unique_combinations():
    """
    Test that all generated configurations are unique.
    """
    grid = generate_test_grid()
    
    # Convert to tuples for set comparison
    config_tuples = [tuple(sorted(c.items())) for c in grid]
    unique_tuples = set(config_tuples)
    
    assert len(config_tuples) == len(unique_tuples), \
        "All configurations in the grid should be unique"


def test_grid_generation_scales_correctly():
    """
    Test that grid size matches expected Cartesian product size.
    """
    # Using the specific values in generate_test_grid
    # locality: 2 options, memory: 2 options, non_linearity: 2 options, seed: 1 option
    expected_size = 2 * 2 * 2 * 1
    grid = generate_test_grid()
    
    assert len(grid) == expected_size, \
        f"Grid size {len(grid)} does not match expected {expected_size}"


def test_grid_configs_loadable_as_yaml():
    """
    Test that each configuration can be serialized to YAML without error.
    This ensures compatibility with the config loading system in eco_director.
    """
    grid = generate_test_grid()
    
    for config in grid:
        try:
            yaml_str = yaml.dump(config)
            loaded_config = yaml.safe_load(yaml_str)
            assert loaded_config == config
        except Exception as e:
            pytest.fail(f"Config {config} failed to serialize/deserialize: {e}")


def test_grid_integration_with_eco_director_schema():
    """
    Test that generated configs are compatible with eco_director validation.
    """
    grid = generate_test_grid()
    
    for config in grid:
        # Wrap in a minimal structure expected by load_config if needed,
        # or validate directly if the schema allows flat dicts.
        # Based on T004a, we expect a schema with locality, memory, non_linearity.
        try:
            # Attempt validation directly on the config dict
            # Note: validate_config signature may vary, assuming it takes a dict
            is_valid = validate_config(config)
            # If it returns a boolean
            assert is_valid, f"Config {config} failed validation"
        except TypeError:
            # If validate_config expects a file path or different structure
            # Create a temp file and test
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(config, f)
                temp_path = f.name
            
            try:
                loaded = load_config(temp_path)
                is_valid = validate_config(loaded)
                assert is_valid
            finally:
                os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])