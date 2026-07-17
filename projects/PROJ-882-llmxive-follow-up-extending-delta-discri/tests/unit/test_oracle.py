"""
Unit tests for DelTA coefficient variance checks.

This module verifies that the generated DelTA coefficients meet the 
minimum variance threshold (variance > 1e-9) to ensure numerical stability
and meaningful signal in the oracle outputs.
"""

import json
import math
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import pytest

# Import the schema validation helper from contracts if available, 
# or implement minimal validation logic here
try:
    from contracts.delta_oracle_schema import validate_delta_oracle
except ImportError:
    # Fallback: minimal validation logic if schema module not imported directly
    def validate_delta_oracle(data: Dict[str, Any]) -> bool:
        """Minimal validation for delta oracle structure."""
        if not isinstance(data, dict):
            return False
        if "coefficients" not in data or not isinstance(data["coefficients"], list):
            return False
        return True

def calculate_variance(values: List[float]) -> float:
    """
    Calculate the population variance of a list of numbers.
    
    Args:
        values: List of numeric values
        
    Returns:
        Population variance (float)
    """
    if not values:
        return 0.0
        
    n = len(values)
    if n == 0:
        return 0.0
        
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    return variance

def check_coefficient_variance(coefficients: List[Dict[str, Any]], min_variance: float = 1e-9) -> Dict[str, Any]:
    """
    Check if all DelTA coefficients meet the minimum variance threshold.
    
    Args:
        coefficients: List of coefficient dictionaries with 'coefficient' key
        min_variance: Minimum acceptable variance threshold (default: 1e-9)
        
    Returns:
        Dictionary with validation results
    """
    if not coefficients:
        return {
            "valid": False,
            "error": "No coefficients provided",
            "variance": 0.0,
            "threshold": min_variance
        }
        
    # Extract coefficient values
    values = []
    for item in coefficients:
        if "coefficient" in item:
            val = item["coefficient"]
            if isinstance(val, (int, float)) and not math.isnan(val) and not math.isinf(val):
                values.append(float(val))
    
    if not values:
        return {
            "valid": False,
            "error": "No valid numeric coefficients found",
            "variance": 0.0,
            "threshold": min_variance
        }
        
    variance = calculate_variance(values)
    
    return {
        "valid": variance > min_variance,
        "variance": variance,
        "threshold": min_variance,
        "count": len(values),
        "error": None if variance > min_variance else f"Variance {variance} is below threshold {min_variance}"
    }

class TestDeltaVarianceCheck:
    """Test suite for DelTA coefficient variance validation."""
    
    def test_variance_above_threshold(self):
        """Test that coefficients with variance > 1e-9 pass validation."""
        # Create coefficients with clear variance
        coefficients = [
            {"token_id": 1, "coefficient": 0.5},
            {"token_id": 2, "coefficient": 0.7},
            {"token_id": 3, "coefficient": 0.3},
            {"token_id": 4, "coefficient": 0.9},
            {"token_id": 5, "coefficient": 0.1}
        ]
        
        result = check_coefficient_variance(coefficients)
        
        assert result["valid"] is True
        assert result["variance"] > 1e-9
        assert result["error"] is None
        
    def test_variance_below_threshold(self):
        """Test that coefficients with variance <= 1e-9 fail validation."""
        # Create coefficients with near-zero variance (all nearly identical)
        base_value = 0.5
        coefficients = [
            {"token_id": i, "coefficient": base_value + (i * 1e-10)}
            for i in range(100)
        ]
        
        result = check_coefficient_variance(coefficients)
        
        assert result["valid"] is False
        assert result["variance"] <= 1e-9
        assert result["error"] is not None
        assert "below threshold" in result["error"]
        
    def test_single_coefficient_zero_variance(self):
        """Test that a single coefficient results in zero variance."""
        coefficients = [
            {"token_id": 1, "coefficient": 0.5}
        ]
        
        result = check_coefficient_variance(coefficients)
        
        assert result["valid"] is False
        assert result["variance"] == 0.0
        
    def test_empty_coefficients_list(self):
        """Test that empty coefficients list fails validation."""
        result = check_coefficient_variance([])
        
        assert result["valid"] is False
        assert "No coefficients provided" in result["error"]
        
    def test_coefficients_with_nan(self):
        """Test that coefficients containing NaN are handled correctly."""
        import math
        coefficients = [
            {"token_id": 1, "coefficient": 0.5},
            {"token_id": 2, "coefficient": float('nan')},
            {"token_id": 3, "coefficient": 0.7}
        ]
        
        result = check_coefficient_variance(coefficients)
        
        # Should filter out NaN values and calculate variance from remaining
        assert result["count"] == 2
        assert result["valid"] is True  # Variance of [0.5, 0.7] > 1e-9
        
    def test_coefficients_with_inf(self):
        """Test that coefficients containing infinity are handled correctly."""
        coefficients = [
            {"token_id": 1, "coefficient": 0.5},
            {"token_id": 2, "coefficient": float('inf')},
            {"token_id": 3, "coefficient": 0.7}
        ]
        
        result = check_coefficient_variance(coefficients)
        
        # Should filter out inf values and calculate variance from remaining
        assert result["count"] == 2
        assert result["valid"] is True
        
    def test_integration_with_json_file(self):
        """Test variance check with a real JSON file conforming to schema."""
        # Create a temporary file with valid coefficients
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            data = {
                "coefficients": [
                    {"token_id": 1, "coefficient": 0.1},
                    {"token_id": 2, "coefficient": 0.5},
                    {"token_id": 3, "coefficient": 0.9}
                ]
            }
            json.dump(data, f)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                loaded_data = json.load(f)
            
            result = check_coefficient_variance(loaded_data["coefficients"])
            
            assert result["valid"] is True
            assert result["variance"] > 1e-9
        finally:
            os.unlink(temp_path)
            
    def test_threshold_parameter(self):
        """Test that custom threshold parameter works correctly."""
        coefficients = [
            {"token_id": 1, "coefficient": 0.5},
            {"token_id": 2, "coefficient": 0.5001}  # Small variance
        ]
        
        # With default threshold (1e-9), should pass
        result_default = check_coefficient_variance(coefficients)
        assert result_default["valid"] is True
        
        # With higher threshold, should fail
        result_high = check_coefficient_variance(coefficients, min_variance=1e-4)
        assert result_high["valid"] is False
        assert result_high["variance"] <= 1e-4

if __name__ == "__main__":
    pytest.main([__file__, "-v"])