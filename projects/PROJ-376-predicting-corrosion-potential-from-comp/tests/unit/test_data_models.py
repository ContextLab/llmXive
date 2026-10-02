"""
Unit tests for data model classes (T007).

Tests instantiation with valid and invalid data to ensure Pydantic v2
strict schema enforcement works as expected.
"""
import pytest
from typing import Dict
from pydantic import ValidationError
from code.data.models import AlloyRecord, EnvironmentRecord, CorrosionMeasurement
from code.utils.exceptions import SchemaMismatchError


class TestAlloyRecord:
    """Tests for AlloyRecord class."""

    def test_valid_alloy_record(self):
        """Test instantiation with valid data."""
        data = {
            "alloy_id": "AL-001",
            "composition": {"Fe": 0.70, "Cr": 0.18, "Ni": 0.08},
            "specific_alloy_designation": "304 Stainless Steel"
        }
        record = AlloyRecord(**data)
        assert record.alloy_id == "AL-001"
        assert record.composition["Fe"] == 0.70
        assert record.specific_alloy_designation == "304 Stainless Steel"

    def test_empty_composition_raises(self):
        """Test that empty composition raises SchemaMismatchError."""
        data = {
            "alloy_id": "AL-002",
            "composition": {},
            "specific_alloy_designation": "Test Alloy"
        }
        with pytest.raises(SchemaMismatchError):
            AlloyRecord(**data)

    def test_negative_fraction_raises(self):
        """Test that negative weight fraction raises SchemaMismatchError."""
        data = {
            "alloy_id": "AL-003",
            "composition": {"Fe": -0.1},
            "specific_alloy_designation": "Test Alloy"
        }
        with pytest.raises(SchemaMismatchError):
            AlloyRecord(**data)

    def test_fraction_over_one_raises(self):
        """Test that weight fraction > 1 raises SchemaMismatchError."""
        data = {
            "alloy_id": "AL-004",
            "composition": {"Fe": 1.5},
            "specific_alloy_designation": "Test Alloy"
        }
        with pytest.raises(SchemaMismatchError):
            AlloyRecord(**data)

    def test_empty_alloy_id_raises(self):
        """Test that empty alloy_id raises SchemaMismatchError."""
        data = {
            "alloy_id": "",
            "composition": {"Fe": 0.9},
            "specific_alloy_designation": "Test Alloy"
        }
        with pytest.raises(SchemaMismatchError):
            AlloyRecord(**data)

    def test_empty_designation_raises(self):
        """Test that empty specific_alloy_designation raises SchemaMismatchError."""
        data = {
            "alloy_id": "AL-005",
            "composition": {"Fe": 0.9},
            "specific_alloy_designation": "   "
        }
        with pytest.raises(SchemaMismatchError):
            AlloyRecord(**data)


class TestEnvironmentRecord:
    """Tests for EnvironmentRecord class."""

    def test_valid_environment_record(self):
        """Test instantiation with valid data."""
        data = {
            "ph": 7.0,
            "temperature": 25.0,
            "electrolyte_type": "NaCl"
        }
        record = EnvironmentRecord(**data)
        assert record.ph == 7.0
        assert record.temperature == 25.0
        assert record.electrolyte_type == "NaCl"

    def test_ph_out_of_range_warns_but_passes(self):
        """Test that pH outside 0-14 warns but passes validation."""
        # We expect a warning, but no exception for strict schema unless we enforce bounds.
        # The validator currently allows it with a warning.
        data = {
            "ph": 15.0,
            "temperature": 25.0,
            "electrolyte_type": "Acid"
        }
        # Should not raise
        record = EnvironmentRecord(**data)
        assert record.ph == 15.0

    def test_temperature_below_absolute_zero_raises(self):
        """Test that temperature below absolute zero raises SchemaMismatchError."""
        data = {
            "ph": 7.0,
            "temperature": -300.0,
            "electrolyte_type": "Water"
        }
        with pytest.raises(SchemaMismatchError):
            EnvironmentRecord(**data)

    def test_empty_electrolyte_raises(self):
        """Test that empty electrolyte_type raises SchemaMismatchError."""
        data = {
            "ph": 7.0,
            "temperature": 25.0,
            "electrolyte_type": "   "
        }
        with pytest.raises(SchemaMismatchError):
            EnvironmentRecord(**data)


class TestCorrosionMeasurement:
    """Tests for CorrosionMeasurement class."""

    def test_valid_measurement(self):
        """Test instantiation with valid data."""
        data = {
            "record_id": "REC-001",
            "potential_mV": -250.5
        }
        record = CorrosionMeasurement(**data)
        assert record.record_id == "REC-001"
        assert record.potential_mV == -250.5

    def test_empty_record_id_raises(self):
        """Test that empty record_id raises SchemaMismatchError."""
        data = {
            "record_id": "",
            "potential_mV": -250.5
        }
        with pytest.raises(SchemaMismatchError):
            CorrosionMeasurement(**data)

    def test_whitespace_record_id_strips(self):
        """Test that whitespace in record_id is stripped."""
        data = {
            "record_id": "  REC-002  ",
            "potential_mV": -200.0
        }
        record = CorrosionMeasurement(**data)
        assert record.record_id == "REC-002"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])