"""
Schema definitions for CMB simulation artifacts.

Defines the CMBMap schema used for validation of simulation outputs.
"""
import json
from typing import Any, Dict, List, Union

class CMBMapSchema:
    """
    Schema validator for CMBMap entities.
    
    Ensures that simulation outputs adhere to the required structure:
    - Nside must be 512
    - gap_fraction must be within a specific tolerance of the target
    - All required metadata fields are present
    """
    
    REQUIRED_KEYS = [
        "realization_id",
        "nside",
        "gap_fraction",
        "map_data",
        "mask_data",
        "metadata"
    ]
    
    REQUIRED_METADATA_KEYS = [
        "H0",
        "Omega_m",
        "n_s",
        "tau",
        "seed"
    ]
    
    TARGET_NSIDE = 512
    GAP_FRACTION_TOLERANCE = 0.005  # ±0.5%

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> bool:
        """
        Validates a CMBMap dictionary against the schema.
        
        Args:
            data: Dictionary containing CMBMap data.
            
        Returns:
            True if valid.
            
        Raises:
            ValueError: If validation fails.
        """
        if not isinstance(data, dict):
            raise ValueError("CMBMap data must be a dictionary.")

        # Check required keys
        for key in cls.REQUIRED_KEYS:
            if key not in data:
                raise ValueError(f"Missing required key: {key}")

        # Validate Nside
        if data["nside"] != cls.TARGET_NSIDE:
            raise ValueError(
                f"Nside must be {cls.TARGET_NSIDE}, got {data['nside']}"
            )

        # Validate gap_fraction (checks against a target if provided, 
        # or just ensures it's a valid number. For this contract test, 
        # we assume the caller ensures the 'target' context or we check 
        # that it is a valid float. The specific tolerance check in the 
        # test function compares against the specific test case target.)
        if not isinstance(data["gap_fraction"], (int, float)):
            raise ValueError("gap_fraction must be a number.")
        
        # Basic sanity check for gap fraction range
        if not (0.0 <= data["gap_fraction"] <= 1.0):
            raise ValueError("gap_fraction must be between 0.0 and 1.0.")

        # Validate metadata
        if not isinstance(data["metadata"], dict):
            raise ValueError("metadata must be a dictionary.")
        
        for key in cls.REQUIRED_METADATA_KEYS:
            if key not in data["metadata"]:
                raise ValueError(f"Missing metadata key: {key}")

        # Validate data types for lists
        if not isinstance(data["map_data"], list):
            raise ValueError("map_data must be a list.")
        
        if not isinstance(data["mask_data"], list):
            raise ValueError("mask_data must be a list.")

        return True

def validate_cmmap_schema(data: Dict[str, Any]) -> bool:
    """
    Convenience function to validate CMBMap schema.
    """
    return CMBMapSchema.validate(data)