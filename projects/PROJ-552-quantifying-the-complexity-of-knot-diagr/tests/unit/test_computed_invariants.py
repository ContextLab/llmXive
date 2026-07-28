"""Unit tests for computed invariants module."""
from __future__ import annotations

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.data.computed_invariants import (
    compute_invariants_for_record,
    compute_all_invariants,
    _parse_dowker_code,
    _compute_seifert_circles,
    _compute_arc_index,
    _compute_bridge_number,
    ComputedInvariantResult
)


class TestDowkerCodeParsing:
    """Tests for DT code parsing."""

    def test_parse_simple_dt_code(self):
        """Test parsing a simple DT code."""
        dt_code = "4 6 2"
        result = _parse_dowker_code(dt_code)
        assert result == [4, 6, 2]

    def test_parse_negative_dt_code(self):
        """Test parsing a DT code with negative values."""
        dt_code = "-4 -6 -2"
        result = _parse_dowker_code(dt_code)
        assert result == [-4, -6, -2]

    def test_parse_empty_dt_code(self):
        """Test parsing an empty DT code."""
        assert _parse_dowker_code("") == []
        assert _parse_dowker_code("   ") == []
        assert _parse_dowker_code(None) == []

    def test_parse_dt_code_with_separators(self):
        """Test parsing DT code with various separators."""
        assert _parse_dowker_code("4;6;2") == [4, 6, 2]
        assert _parse_dowker_code("4,6,2") == [4, 6, 2]
        assert _parse_dowker_code("4 6 2") == [4, 6, 2]


class TestSeifertCircleComputation:
    """Tests for Seifert circle computation."""

    def test_compute_seifert_circles_simple(self):
        """Test Seifert circle computation on a simple knot."""
        # Trefoil knot DT code
        dt_code = "4 6 2"
        result = _compute_seifert_circles(dt_code)
        assert result is not None
        assert result > 0

    def test_compute_seifert_circles_empty(self):
        """Test Seifert circle computation with empty DT code."""
        result = _compute_seifert_circles("")
        assert result is None

    def test_compute_seifert_circles_invalid(self):
        """Test Seifert circle computation with invalid DT code."""
        result = _compute_seifert_circles("invalid")
        assert result is None


class TestArcIndexComputation:
    """Tests for arc index computation."""

    def test_compute_arc_index_simple(self):
        """Test arc index computation on a simple knot."""
        dt_code = "4 6 2"
        result = _compute_arc_index(dt_code)
        assert result is not None
        assert result > 0

    def test_compute_arc_index_empty(self):
        """Test arc index computation with empty DT code."""
        result = _compute_arc_index("")
        assert result is None


class TestBridgeNumberComputation:
    """Tests for bridge number computation."""

    def test_compute_bridge_number_simple(self):
        """Test bridge number computation on a simple knot."""
        dt_code = "4 6 2"
        result = _compute_bridge_number(dt_code)
        assert result is not None
        assert result >= 1

    def test_compute_bridge_number_empty(self):
        """Test bridge number computation with empty DT code."""
        result = _compute_bridge_number("")
        assert result is None


class TestComputeInvariantsForRecord:
    """Tests for computing invariants for a single record."""

    def test_compute_with_valid_dt_code(self):
        """Test computing invariants with a valid DT code."""
        record = {
            'dt_code': '4 6 2',
            'crossing_number': 3,
            'name': '3_1'
        }
        result = compute_invariants_for_record(record)

        assert result.computation_status == 'computed'
        assert result.arc_index is not None
        assert result.seifert_circle_count is not None
        assert result.bridge_number is not None
        assert result.error_message is None

    def test_compute_with_missing_dt_code(self):
        """Test computing invariants with missing DT code."""
        record = {
            'dt_code': '',
            'crossing_number': 3,
            'name': '3_1'
        }
        result = compute_invariants_for_record(record)

        assert result.computation_status == 'missing_data'
        assert result.arc_index is None
        assert result.error_message is not None

    def test_compute_with_none_dt_code(self):
        """Test computing invariants with None DT code."""
        record = {
            'dt_code': None,
            'crossing_number': 3,
            'name': '3_1'
        }
        result = compute_invariants_for_record(record)

        assert result.computation_status == 'missing_data'


class TestComputeAllInvariants:
    """Tests for computing invariants for the entire dataset."""

    def test_compute_all_invariants_with_sample_data(self):
        """Test computing invariants on a sample dataset."""
        # Create a temporary CSV file with sample data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("name,dt_code,crossing_number,braid_index\n")
            f.write("3_1,4 6 2,3,2\n")
            f.write("4_1,6 2 8 4,4,2\n")
            f.write("5_1,,5,2\n")  # Missing DT code
            temp_input = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_output = f.name

        try:
            stats = compute_all_invariants(Path(temp_input), Path(temp_output))

            assert stats['total_records'] == 3
            assert stats['computed'] == 2  # Two records with DT codes
            assert stats['missing_data'] == 1  # One record without DT code

            # Verify output file exists and has correct columns
            assert Path(temp_output).exists()
            df = pd.read_csv(temp_output)
            assert 'arc_index' in df.columns
            assert 'seifert_circle_count' in df.columns
            assert 'bridge_number' in df.columns
            assert 'computation_status' in df.columns

            # Check that records with DT codes have computed values
            assert df.iloc[0]['arc_index'] is not None
            assert pd.notna(df.iloc[0]['arc_index'])

            # Check that records without DT codes have NaN
            assert pd.isna(df.iloc[2]['arc_index'])

        finally:
            os.unlink(temp_input)
            os.unlink(temp_output)

    def test_compute_all_invariants_missing_input(self):
        """Test computing invariants when input file is missing."""
        with pytest.raises(FileNotFoundError):
            compute_all_invariants(Path("nonexistent.csv"), Path("output.csv"))


class TestComputedInvariantResult:
    """Tests for the ComputedInvariantResult dataclass."""

    def test_result_creation_computed(self):
        """Test creating a result with computed values."""
        result = ComputedInvariantResult(
            arc_index=5,
            seifert_circle_count=3,
            bridge_number=2,
            computation_status='computed'
        )

        assert result.arc_index == 5
        assert result.seifert_circle_count == 3
        assert result.bridge_number == 2
        assert result.computation_status == 'computed'

    def test_result_creation_missing_data(self):
        """Test creating a result for missing data."""
        result = ComputedInvariantResult(
            computation_status='missing_data',
            error_message='No DT code available'
        )

        assert result.arc_index is None
        assert result.computation_status == 'missing_data'
        assert result.error_message == 'No DT code available'
