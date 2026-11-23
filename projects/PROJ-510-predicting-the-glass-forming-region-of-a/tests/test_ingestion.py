"""
Tests for the ingestion module.
"""
import os
import sys
import json
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from code.ingestion import (
    parse_composition,
    validate_ternary_elements,
    clean_data,
    validate_critical_cooling_rate,
    validate_data_size
)

class TestParseComposition:
    def test_valid_ternary(self):
        """Test parsing a valid ternary composition."""
        result = parse_composition("Fe40Ni40B20")
        assert result is not None
        assert len(result) == 3
        assert result["Fe"] == 40.0
        assert result["Ni"] == 40.0
        assert result["B"] == 20.0

    def test_invalid_composition(self):
        """Test parsing an invalid composition."""
        result = parse_composition("InvalidString")
        assert result is None

    def test_empty_string(self):
        """Test parsing an empty string."""
        result = parse_composition("")
        assert result is None

    def test_binary_alloy(self):
        """Test that binary alloys are parsed correctly (but validation will fail later)."""
        result = parse_composition("Fe50Ni50")
        assert result is not None
        assert len(result) == 2

class TestValidateTernaryElements:
    def test_valid_ternary(self):
        """Test validation of a valid ternary."""
        parsed = {"Fe": 40.0, "Ni": 40.0, "B": 20.0}
        assert validate_ternary_elements(parsed) is True

    def test_binary_alloy(self):
        """Test validation of a binary alloy (should fail)."""
        parsed = {"Fe": 50.0, "Ni": 50.0}
        assert validate_ternary_elements(parsed) is False

    def test_invalid_element(self):
        """Test validation with an invalid element symbol."""
        parsed = {"Fe": 33.3, "Ni": 33.3, "XYZ": 33.4}
        assert validate_ternary_elements(parsed) is False

    def test_empty_dict(self):
        """Test validation of empty dictionary."""
        assert validate_ternary_elements({}) is False

class TestCleanData:
    def test_clean_data_adds_source_label(self):
        """Test that clean_data adds source_label column."""
        df = pd.DataFrame({
            "composition": ["Fe40Ni40B20"],
            "critical_cooling_rate": [100.0]
        })
        cleaned = clean_data(df)
        assert "source_label" in cleaned.columns
        assert cleaned["source_label"].iloc[0] == "matsci/glass-forming-ability"

    def test_clean_data_adds_synthetic_flag(self):
        """Test that clean_data adds is_synthetic column."""
        df = pd.DataFrame({
            "composition": ["Fe40Ni40B20"],
            "critical_cooling_rate": [100.0]
        })
        cleaned = clean_data(df)
        assert "is_synthetic" in cleaned.columns
        assert cleaned["is_synthetic"].iloc[0] is False

class TestValidateCriticalCoolingRate:
    def test_nonzero_variance(self):
        """Test validation with non-zero variance."""
        df = pd.DataFrame({
            "critical_cooling_rate": [100.0, 200.0, 300.0]
        })
        assert validate_critical_cooling_rate(df) is True

    def test_zero_variance(self):
        """Test validation with zero variance."""
        df = pd.DataFrame({
            "critical_cooling_rate": [100.0, 100.0, 100.0]
        })
        with pytest.raises(ValueError, match="Zero variance"):
            validate_critical_cooling_rate(df)

class TestValidateDataSize:
    def test_pass_status(self):
        """Test validation with sufficient data."""
        df = pd.DataFrame({
            "critical_cooling_rate": [100.0] * 1000
        })
        status = validate_data_size(df)
        assert status["status"] == "pass"
        assert status["n_total"] == 1000

    def test_warning_status(self):
        """Test validation with warning-level data."""
        df = pd.DataFrame({
            "critical_cooling_rate": [100.0] * 750
        })
        status = validate_data_size(df)
        assert status["status"] == "warning"
        assert status["n_total"] == 750

    def test_fail_status(self):
        """Test validation with insufficient data."""
        df = pd.DataFrame({
            "critical_cooling_rate": [100.0] * 400
        })
        status = validate_data_size(df)
        assert status["status"] == "fail"
        assert status["n_total"] == 400
