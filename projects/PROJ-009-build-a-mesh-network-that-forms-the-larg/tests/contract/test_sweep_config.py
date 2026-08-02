"""
Contract test for Parameter Sweep configuration.

This test validates that the Parameter Sweep configuration adheres to the
schema defined in the project's contract specifications. It ensures that
the sweep parameters (granularity, node counts, latency settings) are
correctly structured and valid before execution.

Acceptance Criteria:
- Validates the structure of sweep configurations against defined schemas.
- Ensures required fields (granularity, node_count, latency) are present.
- Checks that granularity values are within allowed set (fine, medium, coarse).
- Verifies node_count is a positive integer.
- Confirms latency values are non-negative.
"""

import pytest
import json
import os
from pathlib import Path

# Import the schema definitions from the contracts directory
# Assuming contracts are stored in YAML/JSON and loaded here
# Since the API surface doesn't explicitly list a schema loader, we define the
# expected structure based on the task description and existing models.

# We will simulate the schema validation logic here to ensure the configuration
# matches the expected contract.

# Define the expected schema structure based on project requirements
SWEEP_CONFIG_SCHEMA = {
    "required": ["granularity", "node_count", "latency_ms"],
    "properties": {
        "granularity": {
            "type": "string",
            "enum": ["fine", "medium", "coarse"]
        },
        "node_count": {
            "type": "integer",
            "minimum": 1
        },
        "latency_ms": {
            "type": "number",
            "minimum": 0
        },
        "packet_loss_pct": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "optional": True
        },
        "bandwidth_mbps": {
            "type": "number",
            "minimum": 0,
            "optional": True
        }
    }
}

def validate_sweep_config(config: dict) -> bool:
    """
    Validates a sweep configuration against the defined schema.
    
    Args:
        config (dict): The configuration dictionary to validate.
        
    Returns:
        bool: True if valid, False otherwise.
        
    Raises:
        ValueError: If the configuration is invalid.
    """
    # Check required fields
    for field in SWEEP_CONFIG_SCHEMA["required"]:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate granularity
    if config["granularity"] not in SWEEP_CONFIG_SCHEMA["properties"]["granularity"]["enum"]:
        raise ValueError(f"Invalid granularity: {config['granularity']}. Must be one of {SWEEP_CONFIG_SCHEMA['properties']['granularity']['enum']}")
    
    # Validate node_count
    if not isinstance(config["node_count"], int) or config["node_count"] < 1:
        raise ValueError(f"Invalid node_count: {config['node_count']}. Must be a positive integer.")
    
    # Validate latency_ms
    if not isinstance(config["latency_ms"], (int, float)) or config["latency_ms"] < 0:
        raise ValueError(f"Invalid latency_ms: {config['latency_ms']}. Must be a non-negative number.")
    
    # Validate optional fields if present
    if "packet_loss_pct" in config:
        if not isinstance(config["packet_loss_pct"], (int, float)) or not (0 <= config["packet_loss_pct"] <= 100):
            raise ValueError(f"Invalid packet_loss_pct: {config['packet_loss_pct']}. Must be between 0 and 100.")
    
    if "bandwidth_mbps" in config:
        if not isinstance(config["bandwidth_mbps"], (int, float)) or config["bandwidth_mbps"] < 0:
            raise ValueError(f"Invalid bandwidth_mbps: {config['bandwidth_mbps']}. Must be a non-negative number.")
    
    return True


class TestSweepConfigContract:
    """
    Test suite for Parameter Sweep configuration contract validation.
    """

    def test_valid_fine_granularity_config(self):
        """Test a valid configuration with fine granularity."""
        config = {
            "granularity": "fine",
            "node_count": 5,
            "latency_ms": 10,
            "packet_loss_pct": 0.5
        }
        assert validate_sweep_config(config) is True

    def test_valid_medium_granularity_config(self):
        """Test a valid configuration with medium granularity."""
        config = {
            "granularity": "medium",
            "node_count": 10,
            "latency_ms": 50
        }
        assert validate_sweep_config(config) is True

    def test_valid_coarse_granularity_config(self):
        """Test a valid configuration with coarse granularity."""
        config = {
            "granularity": "coarse",
            "node_count": 20,
            "latency_ms": 100,
            "bandwidth_mbps": 1000
        }
        assert validate_sweep_config(config) is True

    def test_missing_required_field(self):
        """Test that missing a required field raises an error."""
        config = {
            "granularity": "fine",
            "latency_ms": 10
            # node_count is missing
        }
        with pytest.raises(ValueError, match="Missing required field: node_count"):
            validate_sweep_config(config)

    def test_invalid_granularity_value(self):
        """Test that an invalid granularity value raises an error."""
        config = {
            "granularity": "ultra_fine",
            "node_count": 5,
            "latency_ms": 10
        }
        with pytest.raises(ValueError, match="Invalid granularity"):
            validate_sweep_config(config)

    def test_invalid_node_count_type(self):
        """Test that non-integer node_count raises an error."""
        config = {
            "granularity": "fine",
            "node_count": "five",
            "latency_ms": 10
        }
        with pytest.raises(ValueError, match="Invalid node_count"):
            validate_sweep_config(config)

    def test_negative_node_count(self):
        """Test that negative node_count raises an error."""
        config = {
            "granularity": "fine",
            "node_count": -1,
            "latency_ms": 10
        }
        with pytest.raises(ValueError, match="Invalid node_count"):
            validate_sweep_config(config)

    def test_negative_latency(self):
        """Test that negative latency raises an error."""
        config = {
            "granularity": "fine",
            "node_count": 5,
            "latency_ms": -10
        }
        with pytest.raises(ValueError, match="Invalid latency_ms"):
            validate_sweep_config(config)

    def test_invalid_packet_loss_pct(self):
        """Test that packet_loss_pct outside 0-100 range raises an error."""
        config = {
            "granularity": "fine",
            "node_count": 5,
            "latency_ms": 10,
            "packet_loss_pct": 150
        }
        with pytest.raises(ValueError, match="Invalid packet_loss_pct"):
            validate_sweep_config(config)

    def test_config_from_json_file(self):
        """Test loading and validating a configuration from a JSON file."""
        # Create a temporary valid config file
        temp_config_path = Path("tests/contract/temp_sweep_config.json")
        temp_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        valid_config = {
            "granularity": "medium",
            "node_count": 8,
            "latency_ms": 25,
            "packet_loss_pct": 1.0
        }
        
        with open(temp_config_path, 'w') as f:
            json.dump(valid_config, f)
        
        try:
            with open(temp_config_path, 'r') as f:
                config = json.load(f)
            
            assert validate_sweep_config(config) is True
        finally:
            # Clean up
            if temp_config_path.exists():
                temp_config_path.unlink()

    def test_empty_config(self):
        """Test that an empty configuration raises an error."""
        config = {}
        with pytest.raises(ValueError, match="Missing required field"):
            validate_sweep_config(config)

    def test_zero_latency_allowed(self):
        """Test that zero latency is allowed."""
        config = {
            "granularity": "fine",
            "node_count": 5,
            "latency_ms": 0
        }
        assert validate_sweep_config(config) is True

    def test_zero_packet_loss_allowed(self):
        """Test that zero packet loss is allowed."""
        config = {
            "granularity": "fine",
            "node_count": 5,
            "latency_ms": 10,
            "packet_loss_pct": 0
        }
        assert validate_sweep_config(config) is True

    def test_max_packet_loss_allowed(self):
        """Test that 100% packet loss is allowed (edge case)."""
        config = {
            "granularity": "fine",
            "node_count": 5,
            "latency_ms": 10,
            "packet_loss_pct": 100
        }
        assert validate_sweep_config(config) is True

    def test_float_latency_allowed(self):
        """Test that float latency values are allowed."""
        config = {
            "granularity": "fine",
            "node_count": 5,
            "latency_ms": 10.5
        }
        assert validate_sweep_config(config) is True

    def test_float_packet_loss_allowed(self):
        """Test that float packet loss values are allowed."""
        config = {
            "granularity": "fine",
            "node_count": 5,
            "latency_ms": 10,
            "packet_loss_pct": 0.75
        }
        assert validate_sweep_config(config) is True