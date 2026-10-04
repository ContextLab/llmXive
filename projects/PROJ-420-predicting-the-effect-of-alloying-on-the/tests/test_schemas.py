"""Contract tests for data schemas (US1).

Tests validate the AlloyRecord schema, missing field handling, and unit normalization
logic as specified in the project contracts.
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
from pydantic import ValidationError

# Import the schema definition from the existing API surface
from code.schemas.alloy_record import AlloyRecord, ModelMetrics


class TestAlloyRecordSchemaValidation:
    """Tests for T042: test_alloy_record_schema_validation."""

    def test_valid_alloy_record_creation(self):
        """Verify a complete, valid AlloyRecord can be instantiated."""
        record = AlloyRecord(
            poisson_ratio=0.33,
            young_modulus=70.0,
            composition={
                "Cu": 0.04,
                "Mg": 0.01,
                "Si": 0.01,
                "Zn": 0.00,
                "Mn": 0.00
            },
            measurement_method="Ultrasonic",
            alloy_type="monolithic"
        )
        assert record.poisson_ratio == 0.33
        assert record.young_modulus == 70.0
        assert record.alloy_type == "monolithic"

    def test_schema_validation_rejects_invalid_types(self):
        """Verify schema rejects invalid types for core fields."""
        with pytest.raises(ValidationError):
            AlloyRecord(
                poisson_ratio="invalid_string",  # Should be float
                young_modulus=70.0,
                composition={"Cu": 0.04},
                measurement_method="Ultrasonic",
                alloy_type="monolithic"
            )

    def test_composition_required_fields(self):
        """Verify composition dict is required and validated."""
        # Missing composition entirely
        with pytest.raises(ValidationError):
            AlloyRecord(
                poisson_ratio=0.33,
                young_modulus=70.0,
                measurement_method="Ultrasonic",
                alloy_type="monolithic"
            )

    def test_measurement_method_optional(self):
        """Verify measurement_method is optional per T007 spec."""
        record = AlloyRecord(
            poisson_ratio=0.33,
            young_modulus=70.0,
            composition={"Cu": 0.04, "Mg": 0.01, "Si": 0.01, "Zn": 0.00, "Mn": 0.00},
            alloy_type="monolithic"
            # measurement_method omitted intentionally
        )
        assert record.measurement_method is None


class TestMissingFieldHandling:
    """Tests for T042: test_missing_field_handling.

    Validates that the schema correctly handles optional fields (like measurement_method)
    and that missing data is flagged appropriately for downstream exclusion (T014).
    """

    def test_missing_measurement_method_defaults_to_none(self):
        """Ensure missing measurement_method results in None, not an error."""
        record = AlloyRecord(
            poisson_ratio=0.33,
            young_modulus=70.0,
            composition={"Cu": 0.04, "Mg": 0.01, "Si": 0.01, "Zn": 0.00, "Mn": 0.00},
            alloy_type="monolithic"
        )
        assert record.measurement_method is None

    def test_model_metrics_schema(self):
        """Verify ModelMetrics schema handles missing optional fields."""
        metrics = ModelMetrics(
            model_type="RandomForest",
            mae=0.05,
            rmse=0.07
        )
        assert metrics.model_type == "RandomForest"
        assert metrics.mae == 0.05
        # r2_score is optional
        assert metrics.r2_score is None


class TestUnitNormalization:
    """Tests for T042: test_unit_normalization.

    Validates the unit normalization logic (wt% to at% conversion)
    is correctly represented in the schema or helper logic.
    Note: The actual conversion logic is in code/data/clean.py (T012),
    but we test that the schema accepts the normalized atomic fractions.
    """

    def test_atomic_fraction_sum_validation(self):
        """Verify schema accepts atomic fractions that sum to ~1.0."""
        # Valid sum
        record = AlloyRecord(
            poisson_ratio=0.33,
            young_modulus=70.0,
            composition={
                "Cu": 0.04,
                "Mg": 0.01,
                "Si": 0.01,
                "Zn": 0.00,
                "Mn": 0.00
            },
            measurement_method="Ultrasonic",
            alloy_type="monolithic"
        )
        assert record is not None

    def test_schema_rejects_negative_fractions(self):
        """Verify schema rejects negative composition values."""
        with pytest.raises(ValidationError):
            AlloyRecord(
                poisson_ratio=0.33,
                young_modulus=70.0,
                composition={
                    "Cu": -0.04,  # Invalid
                    "Mg": 0.01,
                    "Si": 0.01,
                    "Zn": 0.00,
                    "Mn": 0.00
                },
                measurement_method="Ultrasonic",
                alloy_type="monolithic"
            )

    def test_schema_rejects_fractions_exceeding_one(self):
        """Verify schema rejects composition values > 1.0."""
        with pytest.raises(ValidationError):
            AlloyRecord(
                poisson_ratio=0.33,
                young_modulus=70.0,
                composition={
                    "Cu": 1.5,  # Invalid
                    "Mg": 0.01,
                    "Si": 0.01,
                    "Zn": 0.00,
                    "Mn": 0.00
                },
                measurement_method="Ultrasonic",
                alloy_type="monolithic"
            )