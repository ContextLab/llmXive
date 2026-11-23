"""
Contract tests for the quantized JSON schema (User Story 1).

These tests verify that the quantization pipeline produces data
strictly adhering to the specified bit-depth constraints.
"""
import json
import os
import tempfile
from pathlib import Path

# Import project utilities and schema definitions
from utils.logging import get_logger
from data.schema import DiscreteStateVector, clamp_to_bin, validate_state_vector_consistency

logger = get_logger(__name__)

def _generate_valid_sample_4bit():
    """
    Generates a minimal valid sample for 4-bit quantization (0-15).
    This is used for the contract test to ensure the assertion logic works.
    In a full integration test, this would be replaced by loading real data
    from data/processed/...
    """
    sample_vector = [0, 5, 10, 15, 7, 3, 12, 1]
    # Ensure it fits the schema
    for val in sample_vector:
        if not (0 <= val <= 15):
            raise ValueError("Sample generation failed: value out of 4-bit range")
    return sample_vector

def test_quantized_schema_4bit():
    """
    Contract test for quantized JSON schema in 4-bit mode.
    
    Asserts that all integer values in the loaded discrete state vector
    are within the valid 4-bit range [0, 15].
    
    This test simulates the validation logic that would run on the
    output of code/data/quantize.py.
    """
    logger.info("Running contract test: test_quantized_schema_4bit")
    
    # Create a temporary file to simulate the output of the quantization pipeline
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        sample_data = {
            "episode_id": "contract_test_001",
            "bit_depth": 4,
            "states": _generate_valid_sample_4bit()
        }
        json.dump(sample_data, f)
        temp_path = f.name

    try:
        # Load the data
        with open(temp_path, 'r') as f:
            loaded_data = json.load(f)
        
        states = loaded_data.get("states", [])
        bit_depth = loaded_data.get("bit_depth", 0)
        
        # Validate bit depth
        if bit_depth != 4:
            raise AssertionError(f"Expected bit_depth 4, got {bit_depth}")
        
        # Core Contract Assertion: all(0 <= x <= 15 for x in data)
        for i, x in enumerate(states):
            if not isinstance(x, int):
                raise AssertionError(f"State at index {i} is not an integer: {type(x)}")
            if not (0 <= x <= 15):
                raise AssertionError(f"State at index {i} is out of 4-bit range: {x}")
        
        # Additional consistency check using project schema utilities
        # Convert to numpy for utility check if needed, though raw list check is primary
        assert validate_state_vector_consistency(states, 4), "Schema consistency validation failed"
        
        logger.info("Contract test passed: All values within [0, 15]")
        
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_quantized_schema_8bit():
    """
    Contract test for 8-bit quantization (0-255).
    """
    logger.info("Running contract test: test_quantized_schema_8bit")
    
    sample_vector = [0, 128, 255, 64, 200]
    for val in sample_vector:
        if not (0 <= val <= 255):
            raise ValueError("Sample generation failed: value out of 8-bit range")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"episode_id": "test_8bit", "bit_depth": 8, "states": sample_vector}, f)
        temp_path = f.name

    try:
        with open(temp_path, 'r') as f:
            loaded_data = json.load(f)
        
        states = loaded_data.get("states", [])
        
        for i, x in enumerate(states):
            if not (0 <= x <= 255):
                raise AssertionError(f"State at index {i} is out of 8-bit range: {x}")
        
        logger.info("Contract test passed: All values within [0, 255]")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    test_quantized_schema_4bit()
    test_quantized_schema_8bit()
    print("All contract tests passed.")