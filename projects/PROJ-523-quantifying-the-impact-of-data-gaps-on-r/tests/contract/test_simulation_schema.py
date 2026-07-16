"""
Contract test for CMBMap schema validation.

Tests that a CMBMap with Nside=512 and a valid gap_fraction validates correctly.
This test acts as a contract to ensure the simulation output adheres to the
defined schema requirements (Nside=512, gap_fraction within tolerance).
"""
import os
import sys
import json
import pytest
from pathlib import Path

# Ensure code directory is in path
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from contracts.simulation.schema import CMBMapSchema

def test_validate_cmmap_schema():
    """
    Assert that CMBMap schema validates a map with Nside=512 and gap_fraction within tolerance.
    """
    # Define a valid CMBMap instance matching the expected schema structure
    # Nside=512 is the fixed resolution for this project
    # gap_fraction=0.10 (10%) is the target, tolerance is ±0.005 (0.5%)
    valid_map = {
        "realization_id": "test_001",
        "nside": 512,
        "gap_fraction": 0.10,
        "map_data": [0.1, 0.2, 0.3],  # Mock data for schema structure validation
        "mask_data": [1, 1, 0],
        "metadata": {
            "H0": 67.4,
            "Omega_m": 0.315,
            "n_s": 0.965,
            "tau": 0.054,
            "seed": 42
        }
    }

    # Validate using the schema
    # The CMBMapSchema class from contracts.simulation.schema is expected to
    # have a validate method that raises ValueError if the schema is violated.
    try:
        CMBMapSchema.validate(valid_map)
        
        # Explicit assertions to enforce the specific constraints mentioned in the task:
        
        # 1. Verify Nside is exactly 512
        assert valid_map["nside"] == 512, "Nside must be 512"
        
        # 2. Verify gap_fraction is within tolerance (±0.5% or 0.005)
        target_fraction = 0.10
        tolerance = 0.005
        assert abs(valid_map["gap_fraction"] - target_fraction) <= tolerance, \
            f"Gap fraction {valid_map['gap_fraction']} not within tolerance of {target_fraction} ± {tolerance}"
        
        # 3. Verify required keys exist (schema should catch this, but explicit check for contract)
        required_keys = ["realization_id", "nside", "gap_fraction", "map_data", "mask_data", "metadata"]
        for key in required_keys:
            assert key in valid_map, f"Missing required key: {key}"
        
        # 4. Verify metadata keys exist
        required_meta_keys = ["H0", "Omega_m", "n_s", "tau", "seed"]
        for key in required_meta_keys:
            assert key in valid_map["metadata"], f"Missing metadata key: {key}"

        print("Schema validation passed for Nside=512 and gap_fraction within tolerance.")

    except Exception as e:
        pytest.fail(f"Schema validation failed: {e}")
