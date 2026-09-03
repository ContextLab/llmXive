"""
Unit tests for the Metallic Glass dataset schema validation (T006).
Tests the Pydantic models and schema compliance.
"""
import pytest
from typing import Dict, Any
from code.features.dataset_models import MetallicGlassEntry, DataSource, AlloyFamily, validate_entry_to_model

# Valid sample data
VALID_ENTRY: Dict[str, Any] = {
    "composition": "Zr50Cu40Al10",
    "cte": 12.5,
    "amorphous_flag": True,
    "mean_atomic_radius": 147.2,
    "electronegativity_var": 0.05,
    "vec": 3.2,
    "size_mismatch": 0.08,
    "source": "materials_project",
    "alloy_family": "Zr"
}

def test_valid_entry_creation():
    """Test that a valid entry can be created."""
    entry = MetallicGlassEntry(**VALID_ENTRY)
    assert entry.composition == "Zr50Cu40Al10"
    assert entry.amorphous_flag is True
    assert entry.source == DataSource.MATERIALS_PROJECT
    assert entry.alloy_family == AlloyFamily.ZR

def test_validate_entry_to_model_success():
    """Test the helper function with valid data."""
    entry = validate_entry_to_model(VALID_ENTRY)
    assert isinstance(entry, MetallicGlassEntry)
    assert entry.vec == 3.2

def test_invalid_composition_format():
    """Test that invalid chemical formulas are rejected."""
    invalid_data = VALID_ENTRY.copy()
    invalid_data["composition"] = "Zr-Cu-Al" # Invalid format
    
    with pytest.raises(ValueError) as exc_info:
        validate_entry_to_model(invalid_data)
    assert "Invalid chemical formula format" in str(exc_info.value)

def test_non_amorphous_rejected():
    """Test that non-amorphous entries are rejected."""
    invalid_data = VALID_ENTRY.copy()
    invalid_data["amorphous_flag"] = False
    
    with pytest.raises(ValueError) as exc_info:
        validate_entry_to_model(invalid_data)
    assert "Only amorphous entries" in str(exc_info.value)

def test_nan_values_rejected():
    """Test that NaN values are rejected."""
    import math
    invalid_data = VALID_ENTRY.copy()
    invalid_data["cte"] = float('nan')
    
    with pytest.raises(ValueError) as exc_info:
        validate_entry_to_model(invalid_data)
    assert "must be finite" in str(exc_info.value)

def test_negative_cte_rejected():
    """Test that negative CTE values are rejected."""
    invalid_data = VALID_ENTRY.copy()
    invalid_data["cte"] = -5.0
    
    with pytest.raises(ValueError) as exc_info:
        validate_entry_to_model(invalid_data)
    assert "ge=0.0" in str(exc_info.value) or "greater than or equal to 0" in str(exc_info.value)

def test_size_mismatch_bounds():
    """Test that size_mismatch must be between 0 and 1."""
    invalid_data = VALID_ENTRY.copy()
    invalid_data["size_mismatch"] = 1.5
    
    with pytest.raises(ValueError) as exc_info:
        validate_entry_to_model(invalid_data)
    assert "le=1.0" in str(exc_info.value) or "less than or equal to 1" in str(exc_info.value)

def test_invalid_source():
    """Test that invalid source strings are rejected."""
    invalid_data = VALID_ENTRY.copy()
    invalid_data["source"] = "unknown_source"
    
    with pytest.raises(ValueError) as exc_info:
        validate_entry_to_model(invalid_data)
    assert "Invalid source value" in str(exc_info.value)