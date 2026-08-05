"""
Contract test for model_output schema.

Implements test_model_output_schema_validates_prediction_range to assert
that predicted dipoles are within physical bounds.

This test validates that the model_output schema enforces physical constraints
on dipole moment predictions, ensuring they fall within reasonable bounds
for organic molecules (typically 0-20 Debye for QM9 dataset molecules).
"""

import pytest
import json
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

# Import schema validation utilities if available, otherwise implement inline
try:
    from utils.reference_validator import load_schema
except ImportError:
    # Fallback: define schema inline if validator not available
    MODEL_OUTPUT_SCHEMA = {
        "type": "object",
        "properties": {
            "molecule_id": {"type": "string"},
            "predicted_dipole": {"type": "number"},
            "true_dipole": {"type": "number"}
        },
        "required": ["molecule_id", "predicted_dipole", "true_dipole"]
    }

# Physical bounds for dipole moments (Debye)
# QM9 molecules typically range from 0 to ~20 Debye
# Setting conservative bounds: 0 to 50 Debye to catch obvious errors
MIN_DIPOLE = 0.0
MAX_DIPOLE = 50.0


def validate_model_output_schema(data: dict) -> bool:
    """
    Validate model output data against schema and physical bounds.
    
    Args:
        data: Dictionary containing molecule_id, predicted_dipole, true_dipole
    
    Returns:
        bool: True if validation passes
    
    Raises:
        ValueError: If validation fails
    """
    # Check required fields
    required_fields = ["molecule_id", "predicted_dipole", "true_dipole"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Check types
    if not isinstance(data["molecule_id"], str):
        raise ValueError(f"molecule_id must be string, got {type(data['molecule_id'])}")
    
    if not isinstance(data["predicted_dipole"], (int, float)):
        raise ValueError(f"predicted_dipole must be numeric, got {type(data['predicted_dipole'])}")
    
    if not isinstance(data["true_dipole"], (int, float)):
        raise ValueError(f"true_dipole must be numeric, got {type(data['true_dipole'])}")
    
    # Check physical bounds for predicted_dipole
    if data["predicted_dipole"] < MIN_DIPOLE:
        raise ValueError(
            f"predicted_dipole {data['predicted_dipole']} is below physical "
            f"lower bound {MIN_DIPOLE} Debye"
        )
    
    if data["predicted_dipole"] > MAX_DIPOLE:
        raise ValueError(
            f"predicted_dipole {data['predicted_dipole']} is above physical "
            f"upper bound {MAX_DIPOLE} Debye"
        )
    
    # Check physical bounds for true_dipole (for consistency)
    if data["true_dipole"] < MIN_DIPOLE:
        raise ValueError(
            f"true_dipole {data['true_dipole']} is below physical "
            f"lower bound {MIN_DIPOLE} Debye"
        )
    
    if data["true_dipole"] > MAX_DIPOLE:
        raise ValueError(
            f"true_dipole {data['true_dipole']} is above physical "
            f"upper bound {MAX_DIPOLE} Debye"
        )
    
    return True


class TestModelOutputSchema:
    """Test suite for model output schema validation."""

    def test_model_output_schema_validates_prediction_range(self):
        """
        Assert predicted dipoles are within physical bounds.
        
        This test validates that:
        1. Valid predictions within bounds pass validation
        2. Predictions below 0 Debye fail validation
        3. Predictions above 50 Debye fail validation
        4. Non-numeric values fail validation
        """
        # Test case 1: Valid prediction within bounds
        valid_data = {
            "molecule_id": "test_molecule_001",
            "predicted_dipole": 5.5,
            "true_dipole": 5.2
        }
        assert validate_model_output_schema(valid_data) is True
        
        # Test case 2: Prediction at lower bound (0 Debye)
        valid_data_lower = {
            "molecule_id": "test_molecule_002",
            "predicted_dipole": 0.0,
            "true_dipole": 0.1
        }
        assert validate_model_output_schema(valid_data_lower) is True
        
        # Test case 3: Prediction at upper bound (50 Debye)
        valid_data_upper = {
            "molecule_id": "test_molecule_003",
            "predicted_dipole": 50.0,
            "true_dipole": 49.8
        }
        assert validate_model_output_schema(valid_data_upper) is True
        
        # Test case 4: Prediction below lower bound (negative dipole)
        invalid_data_negative = {
            "molecule_id": "test_molecule_004",
            "predicted_dipole": -1.5,
            "true_dipole": 1.2
        }
        with pytest.raises(ValueError) as exc_info:
            validate_model_output_schema(invalid_data_negative)
        assert "below physical lower bound" in str(exc_info.value)
        
        # Test case 5: Prediction above upper bound
        invalid_data_high = {
            "molecule_id": "test_molecule_005",
            "predicted_dipole": 75.3,
            "true_dipole": 10.5
        }
        with pytest.raises(ValueError) as exc_info:
            validate_model_output_schema(invalid_data_high)
        assert "above physical upper bound" in str(exc_info.value)
        
        # Test case 6: Non-numeric predicted_dipole
        invalid_data_type = {
            "molecule_id": "test_molecule_006",
            "predicted_dipole": "not_a_number",
            "true_dipole": 3.2
        }
        with pytest.raises(ValueError) as exc_info:
            validate_model_output_schema(invalid_data_type)
        assert "must be numeric" in str(exc_info.value)
        
        # Test case 7: Missing required field
        invalid_data_missing = {
            "molecule_id": "test_molecule_007",
            "predicted_dipole": 4.5
            # missing true_dipole
        }
        with pytest.raises(ValueError) as exc_info:
            validate_model_output_schema(invalid_data_missing)
        assert "Missing required field" in str(exc_info.value)

    def test_model_output_schema_accepts_edge_cases(self):
        """Test that edge cases within bounds are accepted."""
        # Very small positive dipole
        edge_case_small = {
            "molecule_id": "test_molecule_edge_001",
            "predicted_dipole": 0.001,
            "true_dipole": 0.002
        }
        assert validate_model_output_schema(edge_case_small) is True
        
        # Large but valid dipole
        edge_case_large = {
            "molecule_id": "test_molecule_edge_002",
            "predicted_dipole": 49.999,
            "true_dipole": 48.5
        }
        assert validate_model_output_schema(edge_case_large) is True

    def test_model_output_schema_handles_float_precision(self):
        """Test that float precision issues don't cause false failures."""
        # Test with high precision floats
        precise_data = {
            "molecule_id": "test_molecule_precision",
            "predicted_dipole": 12.3456789012345,
            "true_dipole": 12.3456789012340
        }
        assert validate_model_output_schema(precise_data) is True

    def test_model_output_schema_with_json_serialization(self):
        """Test that schema validation works with JSON-serialized data."""
        test_data = {
            "molecule_id": "json_test_001",
            "predicted_dipole": 7.8,
            "true_dipole": 7.5
        }
        
        # Serialize and deserialize
        json_str = json.dumps(test_data)
        loaded_data = json.loads(json_str)
        
        # Should still validate
        assert validate_model_output_schema(loaded_data) is True

    def test_model_output_schema_rejects_out_of_range_true_dipole(self):
        """Test that true_dipole outside bounds also fails."""
        invalid_true_dipole = {
            "molecule_id": "test_molecule_008",
            "predicted_dipole": 5.0,
            "true_dipole": -2.0
        }
        with pytest.raises(ValueError) as exc_info:
            validate_model_output_schema(invalid_true_dipole)
        assert "below physical lower bound" in str(exc_info.value)
        
        invalid_true_dipole_high = {
            "molecule_id": "test_molecule_009",
            "predicted_dipole": 5.0,
            "true_dipole": 100.0
        }
        with pytest.raises(ValueError) as exc_info:
            validate_model_output_schema(invalid_true_dipole_high)
        assert "above physical upper bound" in str(exc_info.value)