"""
Unit tests for computed_invariants.py
"""
import pytest
from pathlib import Path
import pandas as pd
import sys
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.computed_invariants import (
    ComputedInvariantResult,
    compute_invariants_for_record,
    _parse_braid_word,
    _parse_dt_code,
    _compute_arc_index_from_braid,
    _compute_seifert_circles_from_dt,
    _compute_bridge_number_from_braid,
)


class TestParseBraidWord:
    def test_simple_braid_word(self):
        """Test parsing a simple braid word."""
        braid = "1 2 -1"
        result = _parse_braid_word(braid)
        assert result == [(1, 1), (2, 1), (1, -1)]

    def test_empty_braid_word(self):
        """Test parsing empty braid word."""
        assert _parse_braid_word("") == []
        assert _parse_braid_word(None) == []

    def test_complex_braid_word(self):
        """Test parsing a complex braid word."""
        braid = "1 2 3 -2 -1 3"
        result = _parse_braid_word(braid)
        assert result == [(1, 1), (2, 1), (3, 1), (2, -1), (1, -1), (3, 1)]


class TestParseDtCode:
    def test_simple_dt_code(self):
        """Test parsing a simple DT code."""
        dt = "1 4 3 8 7 6 5 2"
        result = _parse_dt_code(dt)
        assert result == [1, 4, 3, 8, 7, 6, 5, 2]

    def test_empty_dt_code(self):
        """Test parsing empty DT code."""
        assert _parse_dt_code("") == []
        assert _parse_dt_code(None) == []


class TestComputeArcIndex:
    def test_simple_braid(self):
        """Test arc index computation for a simple braid."""
        braid = "1 2 3"
        result = _compute_arc_index_from_braid(braid)
        assert result == 3

    def test_braid_with_negatives(self):
        """Test arc index with negative crossings."""
        braid = "1 -2 3 -1"
        result = _compute_arc_index_from_braid(braid)
        assert result == 3

    def test_empty_braid(self):
        """Test arc index for empty braid."""
        assert _compute_arc_index_from_braid("") is None


class TestComputeSeifertCircles:
    def test_dt_code(self):
        """Test Seifert circle count estimation."""
        dt = [1, 4, 3, 8, 7, 6, 5, 2]
        result = _compute_seifert_circles_from_dt(dt)
        # Heuristic: crossing_count = 4, so result should be >= 2
        assert result is not None
        assert result >= 2

    def test_empty_dt_code(self):
        """Test Seifert circle count for empty DT code."""
        assert _compute_seifert_circles_from_dt([]) is None
        assert _compute_seifert_circles_from_dt(None) is None


class TestComputeBridgeNumber:
    def test_simple_braid(self):
        """Test bridge number estimation."""
        braid = "1 2 3"
        result = _compute_bridge_number_from_braid(braid)
        # Bridge number <= arc index (3)
        assert result is not None
        assert result <= 3

    def test_empty_braid(self):
        """Test bridge number for empty braid."""
        assert _compute_bridge_number_from_braid("") is None


class TestComputeInvariantsForRecord:
    def test_complete_record(self):
        """Test computation with all data present."""
        record = {
            "knot_id": "3_1",
            "braid_word": "1 2 -1",
            "dt_code": "1 4 3 8 7 6 5 2",
            "crossing_number": 3
        }
        result = compute_invariants_for_record(record)
        assert result.knot_id == "3_1"
        assert result.computation_status == "success"
        # Arc index should be computed
        assert result.arc_index is not None
        # Seifert circles should be computed
        assert result.seifert_circle_count is not None
        # Bridge number should be computed
        assert result.bridge_number is not None

    def test_missing_braid_word(self):
        """Test computation with missing braid word."""
        record = {
            "knot_id": "4_1",
            "braid_word": "",
            "dt_code": "1 6 3 8 5 4 7 2",
            "crossing_number": 4
        }
        result = compute_invariants_for_record(record)
        assert result.knot_id == "4_1"
        assert result.computation_status == "success"
        assert result.arc_index is None
        assert result.seifert_circle_count is not None

    def test_missing_dt_code(self):
        """Test computation with missing DT code."""
        record = {
            "knot_id": "5_1",
            "braid_word": "1 2 3 4 -1 -2",
            "dt_code": "",
            "crossing_number": 5
        }
        result = compute_invariants_for_record(record)
        assert result.knot_id == "5_1"
        assert result.computation_status == "success"
        assert result.arc_index is not None
        assert result.seifert_circle_count is None

    def test_empty_record(self):
        """Test computation with minimal data."""
        record = {
            "knot_id": "test_1",
            "braid_word": "",
            "dt_code": "",
            "crossing_number": 0
        }
        result = compute_invariants_for_record(record)
        assert result.knot_id == "test_1"
        assert result.computation_status == "success"
        assert result.arc_index is None
        assert result.seifert_circle_count is None
        assert result.bridge_number is None


class TestComputedInvariantResult:
    def test_default_values(self):
        """Test default values for ComputedInvariantResult."""
        result = ComputedInvariantResult(knot_id="test")
        assert result.knot_id == "test"
        assert result.arc_index is None
        assert result.seifert_circle_count is None
        assert result.bridge_number is None
        assert result.computation_status == "success"
        assert result.error_message is None

    def test_with_values(self):
        """Test ComputedInvariantResult with values."""
        result = ComputedInvariantResult(
            knot_id="test",
            arc_index=3,
            seifert_circle_count=4,
            bridge_number=2,
            computation_status="success"
        )
        assert result.arc_index == 3
        assert result.seifert_circle_count == 4
        assert result.bridge_number == 2