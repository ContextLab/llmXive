"""
Unit tests for the retrieval output schema mapping and validation.
"""
import pytest
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from retrieval_output_schema import (
    RetrievalOutputSchema,
    map_retrieval_result_to_schema,
    get_schema_columns,
    validate_schema_row
)

def test_map_retrieval_result_to_schema_valid():
    """Test mapping valid retrieval results to schema."""
    result = map_retrieval_result_to_schema(
        planet_id="Test_Planet",
        water_mixing_ratio=-4.2,
        std_dev=0.1,
        is_upper_limit=False,
        snr=15.5,
        resolution=100.0,
        status="CONVERGED"
    )
    
    assert result["planet_id"] == "Test_Planet"
    assert result["log10_water_mixing_ratio"] == -4.2
    assert result["std_dev"] == 0.1
    assert result["is_upper_limit"] is False
    assert result["snr"] == 15.5
    assert result["resolution"] == 100.0
    assert result["status"] == "CONVERGED"

def test_map_retrieval_result_to_schema_upper_limit():
    """Test mapping an upper limit result."""
    result = map_retrieval_result_to_schema(
        planet_id="Low_SNR_Planet",
        water_mixing_ratio=-8.0,
        std_dev=0.5,
        is_upper_limit=True,
        snr=3.0,
        resolution=50.0,
        status="UPPER_LIMIT"
    )
    
    assert result["is_upper_limit"] is True
    assert result["status"] == "UPPER_LIMIT"

def test_map_retrieval_result_to_schema_type_conversion():
    """Test that numeric inputs are converted to float."""
    result = map_retrieval_result_to_schema(
        planet_id="Test",
        water_mixing_ratio="-5.0",  # String input
        std_dev="0.2",
        is_upper_limit=False,
        snr="20.0",
        resolution="100",
        status="OK"
    )
    
    assert isinstance(result["log10_water_mixing_ratio"], float)
    assert isinstance(result["std_dev"], float)
    assert isinstance(result["snr"], float)
    assert isinstance(result["resolution"], float)

def test_map_retrieval_result_to_schema_invalid_planet_id():
    """Test that non-string planet_id raises ValueError."""
    with pytest.raises(ValueError):
        map_retrieval_result_to_schema(
            planet_id=12345,  # Invalid type
            water_mixing_ratio=-4.0,
            std_dev=0.1,
            is_upper_limit=False,
            snr=10.0,
            resolution=50.0,
            status="OK"
        )

def test_get_schema_columns():
    """Test that schema columns are returned in correct order."""
    cols = get_schema_columns()
    expected = [
        "planet_id",
        "log10_water_mixing_ratio",
        "std_dev",
        "is_upper_limit",
        "snr",
        "resolution",
        "status"
    ]
    assert cols == expected

def test_validate_schema_row_valid():
    """Test validation of a valid row."""
    row = map_retrieval_result_to_schema(
        planet_id="Valid",
        water_mixing_ratio=-4.0,
        std_dev=0.1,
        is_upper_limit=False,
        snr=10.0,
        resolution=50.0,
        status="OK"
    )
    assert validate_schema_row(row) is True

def test_validate_schema_row_missing_field():
    """Test validation fails on missing field."""
    row = {
        "planet_id": "Test",
        "log10_water_mixing_ratio": -4.0,
        # Missing std_dev
        "is_upper_limit": False,
        "snr": 10.0,
        "resolution": 50.0,
        "status": "OK"
    }
    assert validate_schema_row(row) is False

def test_validate_schema_row_invalid_type():
    """Test validation fails on invalid type."""
    row = {
        "planet_id": 123,  # Should be string
        "log10_water_mixing_ratio": -4.0,
        "std_dev": 0.1,
        "is_upper_limit": False,
        "snr": 10.0,
        "resolution": 50.0,
        "status": "OK"
    }
    assert validate_schema_row(row) is False

def test_validate_schema_row_non_numeric():
    """Test validation fails on non-numeric fields."""
    row = {
        "planet_id": "Test",
        "log10_water_mixing_ratio": "invalid",
        "std_dev": 0.1,
        "is_upper_limit": False,
        "snr": 10.0,
        "resolution": 50.0,
        "status": "OK"
    }
    assert validate_schema_row(row) is False