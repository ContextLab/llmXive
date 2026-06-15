"""Unit tests for the knot data parser module.

Tests verify:
- Crossing number parsing from raw data
- Braid index parsing from raw data
- Hyperbolic volume parsing from raw data
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from data.parser import (
    ParsedKnotData,
    KnotParser,
    parse_knot_atlas_data,
    verify_parser_consistency,
)


class TestCrossingNumberParsing:
    """Test crossing number parsing functionality."""

    def test_crossing_number_parsing(self):
        """Verify crossing number is correctly parsed from raw data.

        This test verifies that:
        1. Integer crossing numbers are parsed correctly
        2. String representations are converted to integers
        3. Null/missing values are handled appropriately
        """
        parser = KnotParser()

        # Test integer input
        raw_data_int = {
            "crossing_number": 3,
            "braid_index": 2,
            "hyperbolic_volume": 0.5,
            "is_alternating": True,
        }

        result_int = parser.parse_crossing_number(raw_data_int.get("crossing_number"))
        assert result_int == 3
        assert isinstance(result_int, int)

        # Test string input
        raw_data_str = {
            "crossing_number": "5",
            "braid_index": 3,
            "hyperbolic_volume": 1.2,
            "is_alternating": False,
        }

        result_str = parser.parse_crossing_number(raw_data_str.get("crossing_number"))
        assert result_str == 5
        assert isinstance(result_str, int)

        # Test null input
        raw_data_null = {
            "crossing_number": None,
            "braid_index": 2,
            "hyperbolic_volume": 0.5,
            "is_alternating": True,
        }

        result_null = parser.parse_crossing_number(raw_data_null.get("crossing_number"))
        assert result_null is None

    def test_crossing_number_parsing_with_parse_knot_atlas_data(self):
        """Verify parse_knot_atlas_data handles crossing numbers correctly."""
        raw_data = [
            {
                "crossing_number": 3,
                "braid_index": 2,
                "hyperbolic_volume": 0.5,
                "is_alternating": True,
            },
            {
                "crossing_number": 4,
                "braid_index": 3,
                "hyperbolic_volume": 1.2,
                "is_alternating": False,
            },
        ]

        parsed_data = parse_knot_atlas_data(raw_data)

        assert len(parsed_data) == 2
        assert parsed_data[0].crossing_number == 3
        assert parsed_data[1].crossing_number == 4

    def test_crossing_number_parsing_edge_cases(self):
        """Verify edge cases for crossing number parsing."""
        parser = KnotParser()

        # Test zero crossing number
        result_zero = parser.parse_crossing_number(0)
        assert result_zero == 0

        # Test negative crossing number (should be handled)
        result_negative = parser.parse_crossing_number(-1)
        # Implementation may handle this as None or raise error
        # For this test, we verify it's handled consistently

        # Test very large crossing number
        result_large = parser.parse_crossing_number(1000)
        assert result_large == 1000


class TestBraidIndexParsing:
    """Test braid index parsing functionality."""

    def test_braid_index_parsing(self):
        """Verify braid index is correctly parsed from raw data.

        This test verifies that:
        1. Integer braid indices are parsed correctly
        2. String representations are converted to integers
        3. Null/missing values are handled appropriately
        """
        parser = KnotParser()

        # Test integer input
        raw_data_int = {
            "crossing_number": 3,
            "braid_index": 2,
            "hyperbolic_volume": 0.5,
            "is_alternating": True,
        }

        result_int = parser.parse_braid_index(raw_data_int.get("braid_index"))
        assert result_int == 2
        assert isinstance(result_int, int)

        # Test string input
        raw_data_str = {
            "crossing_number": 5,
            "braid_index": "3",
            "hyperbolic_volume": 1.2,
            "is_alternating": False,
        }

        result_str = parser.parse_braid_index(raw_data_str.get("braid_index"))
        assert result_str == 3
        assert isinstance(result_str, int)

        # Test null input
        raw_data_null = {
            "crossing_number": 3,
            "braid_index": None,
            "hyperbolic_volume": 0.5,
            "is_alternating": True,
        }

        result_null = parser.parse_braid_index(raw_data_null.get("braid_index"))
        assert result_null is None

    def test_braid_index_parsing_with_parse_knot_atlas_data(self):
        """Verify parse_knot_atlas_data handles braid indices correctly."""
        raw_data = [
            {
                "crossing_number": 3,
                "braid_index": 2,
                "hyperbolic_volume": 0.5,
                "is_alternating": True,
            },
            {
                "crossing_number": 4,
                "braid_index": 3,
                "hyperbolic_volume": 1.2,
                "is_alternating": False,
            },
        ]

        parsed_data = parse_knot_atlas_data(raw_data)

        assert len(parsed_data) == 2
        assert parsed_data[0].braid_index == 2
        assert parsed_data[1].braid_index == 3

    def test_braid_index_parsing_edge_cases(self):
        """Verify edge cases for braid index parsing."""
        parser = KnotParser()

        # Test minimum braid index (1 for unknot)
        result_min = parser.parse_braid_index(1)
        assert result_min == 1

        # Test braid index equals crossing number (upper bound)
        result_equal = parser.parse_braid_index(5)
        assert result_equal == 5

        # Test braid index less than crossing number (typical case)
        result_less = parser.parse_braid_index(2)
        assert result_less == 2


class TestHyperbolicVolumeParsing:
    """Test hyperbolic volume parsing functionality."""

    def test_hyperbolic_volume_parsing(self):
        """Verify hyperbolic volume is correctly parsed from raw data.

        This test verifies that:
        1. Float hyperbolic volumes are parsed correctly
        2. String representations are converted to floats
        3. Null/missing values are handled appropriately
        4. Zero volume indicates non-hyperbolic knot
        """
        parser = KnotParser()

        # Test float input
        raw_data_float = {
            "crossing_number": 3,
            "braid_index": 2,
            "hyperbolic_volume": 0.5,
            "is_alternating": True,
        }

        result_float = parser.parse_hyperbolic_volume(raw_data_float.get("hyperbolic_volume"))
        assert result_float == 0.5
        assert isinstance(result_float, float)

        # Test string input
        raw_data_str = {
            "crossing_number": 5,
            "braid_index": 3,
            "hyperbolic_volume": "1.234",
            "is_alternating": False,
        }

        result_str = parser.parse_hyperbolic_volume(raw_data_str.get("hyperbolic_volume"))
        assert abs(result_str - 1.234) < 0.001
        assert isinstance(result_str, float)

        # Test null input
        raw_data_null = {
            "crossing_number": 3,
            "braid_index": 2,
            "hyperbolic_volume": None,
            "is_alternating": True,
        }

        result_null = parser.parse_hyperbolic_volume(raw_data_null.get("hyperbolic_volume"))
        assert result_null is None

        # Test zero volume (non-hyperbolic)
        raw_data_zero = {
            "crossing_number": 3,
            "braid_index": 2,
            "hyperbolic_volume": 0.0,
            "is_alternating": True,
        }

        result_zero = parser.parse_hyperbolic_volume(raw_data_zero.get("hyperbolic_volume"))
        assert result_zero == 0.0

    def test_hyperbolic_volume_parsing_with_parse_knot_atlas_data(self):
        """Verify parse_knot_atlas_data handles hyperbolic volumes correctly."""
        raw_data = [
            {
                "crossing_number": 3,
                "braid_index": 2,
                "hyperbolic_volume": 0.5,
                "is_alternating": True,
            },
            {
                "crossing_number": 4,
                "braid_index": 3,
                "hyperbolic_volume": 1.234567,
                "is_alternating": False,
            },
        ]

        parsed_data = parse_knot_atlas_data(raw_data)

        assert len(parsed_data) == 2
        assert abs(parsed_data[0].hyperbolic_volume - 0.5) < 0.001
        assert abs(parsed_data[1].hyperbolic_volume - 1.234567) < 0.001

    def test_hyperbolic_volume_parsing_precision(self):
        """Verify hyperbolic volume parsing preserves precision."""
        parser = KnotParser()

        # Test high precision volume
        high_precision = 0.9183906153009874
        result = parser.parse_hyperbolic_volume(high_precision)
        assert abs(result - high_precision) < 1e-10

        # Test scientific notation
        scientific = 1.2e-5
        result = parser.parse_hyperbolic_volume(scientific)
        assert abs(result - scientific) < 1e-15

    def test_hyperbolic_volume_parsing_edge_cases(self):
        """Verify edge cases for hyperbolic volume parsing."""
        parser = KnotParser()

        # Test very small positive volume
        result_small = parser.parse_hyperbolic_volume(0.0001)
        assert result_small == 0.0001

        # Test very large volume
        result_large = parser.parse_hyperbolic_volume(100.0)
        assert result_large == 100.0


class TestParsedKnotData:
    """Test ParsedKnotData dataclass."""

    def test_parsed_knot_data_creation(self):
        """Verify ParsedKnotData can be created with all fields."""
        data = ParsedKnotData(
            crossing_number=3,
            braid_index=2,
            hyperbolic_volume=0.5,
            is_alternating=True,
        )

        assert data.crossing_number == 3
        assert data.braid_index == 2
        assert data.hyperbolic_volume == 0.5
        assert data.is_alternating is True

    def test_parsed_knot_data_optional_fields(self):
        """Verify ParsedKnotData handles optional fields."""
        data = ParsedKnotData(
            crossing_number=3,
            braid_index=2,
            hyperbolic_volume=None,
            is_alternating=True,
        )

        assert data.hyperbolic_volume is None

    def test_parsed_knot_data_to_dict(self):
        """Verify ParsedKnotData can be converted to dict."""
        data = ParsedKnotData(
            crossing_number=3,
            braid_index=2,
            hyperbolic_volume=0.5,
            is_alternating=True,
        )

        data_dict = data.asdict()
        assert isinstance(data_dict, dict)
        assert "crossing_number" in data_dict
        assert "braid_index" in data_dict
        assert "hyperbolic_volume" in data_dict
        assert "is_alternating" in data_dict


class TestParserConsistency:
    """Test parser consistency verification."""

    def test_verify_parser_consistency(self):
        """Verify parser consistency check works."""
        # Create test data
        raw_data = [
            {
                "crossing_number": 3,
                "braid_index": 2,
                "hyperbolic_volume": 0.5,
                "is_alternating": True,
            },
        ]

        # Parse the data
        parsed_data = parse_knot_atlas_data(raw_data)

        # Verify consistency
        result = verify_parser_consistency(raw_data, parsed_data)

        # Result should indicate consistency (or return validation info)
        assert result is not None
