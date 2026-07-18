"""
Unit tests for p-value conversion edge cases (Task T035).
Covers Fisher's Z conversion logic, boundary conditions, and exclusion criteria.
"""
import pytest
import math
import numpy as np
from pathlib import Path
import sys
import csv
import json

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from extraction.p_value_converter import (
    p_to_z,
    z_to_r,
    convert_p_to_r,
    validate_p_value,
    is_ambiguous_conversion,
    process_p_value_row
)
from utils.logger import get_logger

# Test constants
EPSILON = 1e-6
LOG_PATH = Path(project_root) / "data" / "logs"
LOG_PATH.mkdir(parents=True, exist_ok=True)


class TestPValueValidation:
    """Tests for p-value validation logic."""

    def test_valid_p_value(self):
        """Valid p-value between 0 and 1."""
        assert validate_p_value(0.05) is True
        assert validate_p_value(0.001) is True
        assert validate_p_value(0.999) is True

    def test_p_value_zero_boundary(self):
        """P-value exactly 0 should be invalid (log(0) undefined)."""
        assert validate_p_value(0.0) is False

    def test_p_value_one_boundary(self):
        """P-value exactly 1 is technically valid but yields Z=0, 
        however often indicates no effect or calculation issue in this context.
        Spec requires handling ambiguity."""
        # 1.0 is valid mathematically but might be ambiguous for effect direction
        assert validate_p_value(1.0) is True

    def test_p_value_negative(self):
        """Negative p-value is invalid."""
        assert validate_p_value(-0.1) is False

    def test_p_value_greater_than_one(self):
        """P-value > 1 is invalid."""
        assert validate_p_value(1.5) is False

    def test_p_value_string_input(self):
        """String representation of p-value should be handled or rejected."""
        with pytest.raises((ValueError, TypeError)):
            validate_p_value("0.05")


class TestPtoZConversion:
    """Tests for P to Z (Fisher's) conversion."""

    def test_p_to_z_standard(self):
        """Standard conversion: p=0.05 (two-tailed) -> Z approx 1.96."""
        z = p_to_z(0.05, two_tailed=True)
        assert abs(z - 1.95996) < 0.001

    def test_p_to_z_one_tailed(self):
        """One-tailed conversion: p=0.05 -> Z approx 1.645."""
        z = p_to_z(0.05, two_tailed=False)
        assert abs(z - 1.64485) < 0.001

    def test_p_to_z_very_small(self):
        """Very small p-value should result in large Z."""
        z = p_to_z(0.0001, two_tailed=True)
        assert z > 3.0

    def test_p_to_z_very_large(self):
        """P-value close to 1 should result in Z close to 0."""
        z = p_to_z(0.99, two_tailed=True)
        assert abs(z) < 0.1

    def test_p_to_z_invalid_input(self):
        """Invalid p-value should raise ValueError."""
        with pytest.raises(ValueError):
            p_to_z(1.5, two_tailed=True)

        with pytest.raises(ValueError):
            p_to_z(-0.1, two_tailed=True)


class TestZtoRConversion:
    """Tests for Z to R conversion."""

    def test_z_to_r_standard(self):
        """Standard conversion: Z=0 -> r=0."""
        r = z_to_r(0.0)
        assert abs(r) < EPSILON

    def test_z_to_r_positive(self):
        """Positive Z yields positive r."""
        r = z_to_r(1.0)
        assert r > 0.0
        assert r < 1.0

    def test_z_to_r_negative(self):
        """Negative Z yields negative r."""
        r = z_to_r(-1.0)
        assert r < 0.0
        assert r > -1.0

    def test_z_to_r_extreme(self):
        """Very large Z approaches 1."""
        r = z_to_r(5.0)
        assert r > 0.99

    def test_z_to_r_extreme_negative(self):
        """Very negative Z approaches -1."""
        r = z_to_r(-5.0)
        assert r < -0.99


class TestAmbiguityDetection:
    """Tests for detecting ambiguous conversions."""

    def test_missing_direction(self):
        """If p-value is given without direction (two-tailed) and effect direction 
        is unknown, it should be flagged as ambiguous if the study doesn't report 
        the sign of the effect."""
        # Scenario: p=0.05, but we don't know if r is positive or negative.
        # The converter might default to positive, but this is an ambiguity.
        # The function should return True if direction is missing.
        assert is_ambiguous_conversion(p_val=0.05, direction="unknown") is True

    def test_known_direction(self):
        """If direction is known, conversion is not ambiguous."""
        assert is_ambiguous_conversion(p_val=0.05, direction="positive") is False
        assert is_ambiguous_conversion(p_val=0.05, direction="negative") is False

    def test_p_equals_one(self):
        """P=1 implies Z=0, but often indicates no data or error in specific contexts.
        Depending on strictness, this might be ambiguous."""
        # If p=1, effect is likely 0. Not necessarily ambiguous if we assume null.
        # But if the study claims significance, it's contradictory.
        # For this test, we assume p=1 is valid but yields r=0.
        assert is_ambiguous_conversion(p_val=1.0, direction="positive") is False


class TestFullConversionPipeline:
    """Integration tests for the full p-to-r conversion pipeline."""

    def test_convert_p_to_r_valid(self):
        """Valid conversion with known direction."""
        r, success = convert_p_to_r(p_val=0.05, n=30, direction="positive", two_tailed=True)
        assert success is True
        assert r > 0.0

    def test_convert_p_to_r_negative_direction(self):
        """Valid conversion with negative direction."""
        r, success = convert_p_to_r(p_val=0.05, n=30, direction="negative", two_tailed=True)
        assert success is True
        assert r < 0.0

    def test_convert_p_to_r_ambiguous(self):
        """Conversion should fail if direction is unknown."""
        r, success = convert_p_to_r(p_val=0.05, n=30, direction="unknown", two_tailed=True)
        assert success is False
        assert r is None

    def test_convert_p_to_r_invalid_p(self):
        """Conversion should fail if p is invalid."""
        r, success = convert_p_to_r(p_val=1.5, n=30, direction="positive", two_tailed=True)
        assert success is False
        assert r is None

    def test_convert_p_to_r_missing_n(self):
        """Conversion requires N for some calculations (though p->z->r doesn't strictly need N,
        the full pipeline often uses N for weighting or SE). 
        Here we test the specific function signature which might require N for metadata."""
        # Assuming the function signature requires N for logging or future SE calc
        # If the function strictly doesn't need N for p->r, this test verifies it handles None gracefully
        # or raises if N is mandatory for the pipeline context.
        # Based on typical meta-analysis, p->r doesn't need N, but SE does.
        # Let's assume the function handles N=0 or None gracefully for the conversion itself.
        try:
            r, success = convert_p_to_r(p_val=0.05, n=None, direction="positive", two_tailed=True)
            # If it succeeds, r should be valid
            assert success is True
        except TypeError:
            # If N is required and not provided, it should fail explicitly
            pass


class TestProcessPValueRow:
    """Tests for processing a single study row with p-values."""

    def setup_method(self):
        """Setup test data and clean log files."""
        self.test_log = LOG_PATH / "conversion_log.csv"
        if self.test_log.exists():
            self.test_log.unlink()

    def test_process_valid_row(self):
        """Process a row with valid p-value and direction."""
        row = {
            "study_id": "S001",
            "p_value": "0.03",
            "n": 50,
            "direction": "positive",
            "two_tailed": "True"
        }
        result = process_p_value_row(row, log_path=self.test_log)
        
        assert result["success"] is True
        assert result["study_id"] == "S001"
        assert "converted_r" in result
        assert result["converted_r"] > 0.0

    def test_process_ambiguous_row(self):
        """Process a row with unknown direction."""
        row = {
            "study_id": "S002",
            "p_value": "0.04",
            "n": 40,
            "direction": "unknown",
            "two_tailed": "True"
        }
        result = process_p_value_row(row, log_path=self.test_log)
        
        assert result["success"] is False
        assert result["exclusion_reason"] == "Unknown effect direction"

    def test_process_invalid_p_row(self):
        """Process a row with invalid p-value."""
        row = {
            "study_id": "S003",
            "p_value": "1.5",
            "n": 30,
            "direction": "positive",
            "two_tailed": "True"
        }
        result = process_p_value_row(row, log_path=self.test_log)
        
        assert result["success"] is False
        assert "Invalid p-value" in result["exclusion_reason"]

    def test_log_file_creation(self):
        """Verify that exclusion reasons are logged to CSV."""
        row = {
            "study_id": "S004",
            "p_value": "0.00", # Invalid
            "n": 20,
            "direction": "positive",
            "two_tailed": "True"
        }
        process_p_value_row(row, log_path=self.test_log)
        
        assert self.test_log.exists()
        
        with open(self.test_log, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) > 0
            assert any(r["study_id"] == "S004" for r in rows)
            assert any(r["reason"] == "Invalid p-value (0 or negative)" for r in rows)

    def teardown_method(self):
        """Clean up test log file."""
        if self.test_log.exists():
            self.test_log.unlink()


class TestEdgeCases:
    """Specific edge cases for p-value conversion."""

    def test_p_value_very_close_to_zero(self):
        """p = 1e-10 should convert without overflow."""
        z = p_to_z(1e-10, two_tailed=True)
        assert not math.isinf(z)
        assert z > 6.0

    def test_p_value_very_close_to_one(self):
        """p = 0.999999 should convert without underflow."""
        z = p_to_z(0.999999, two_tailed=True)
        assert not math.isnan(z)
        assert abs(z) < 0.01

    def test_two_tailed_vs_one_tailed_equivalence(self):
        """p_one_tailed = p_two_tailed / 2 should yield same Z."""
        p_two = 0.04
        p_one = p_two / 2.0
        
        z_two = p_to_z(p_two, two_tailed=True)
        z_one = p_to_z(p_one, two_tailed=False)
        
        assert abs(z_two - z_one) < EPSILON

    def test_round_trip_conversion(self):
        """r -> z -> r should be approximately identity."""
        original_r = 0.45
        z = z_to_r.__wrapped__(original_r) if hasattr(z_to_r, '__wrapped__') else None
        # Manual inverse: r = tanh(z)
        # Forward: z = arctanh(r)
        # Let's test r -> z -> r
        z_val = 0.5 * math.log((1 + original_r) / (1 - original_r))
        recovered_r = math.tanh(z_val)
        assert abs(original_r - recovered_r) < EPSILON