"""
Unit tests for Knot Atlas parser module.

Tests verify:
- Crossing number extraction
- Braid index extraction with tie-breaking rules
- Hyperbolic volume extraction
- Alternating classification
"""
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.parser import (
    KnotParser,
    ParsedKnotData,
    parse_knot_atlas_data,
    verify_parser_consistency
)


class TestKnotParser:
    """Test cases for KnotParser class."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return KnotParser()

    def test_extract_crossing_number(self, parser):
        """Test crossing number extraction from various field names."""
        # Test crossing_number field
        record = {'knot_id': '8_19', 'crossing_number': 8}
        parsed = parser.parse_record(record)
        assert parsed.crossing_number == 8
        assert parsed.knot_id == '8_19'

        # Test crossings field
        record = {'knot_id': '8_19', 'crossings': 8}
        parsed = parser.parse_record(record)
        assert parsed.crossing_number == 8

        # Test c field
        record = {'knot_id': '8_19', 'c': 8}
        parsed = parser.parse_record(record)
        assert parsed.crossing_number == 8

    def test_extract_braid_index_from_braid_word(self, parser):
        """Test braid index extraction from braid word representation."""
        # Braid word "1 2 -1" requires 3 strands (indices 1, 2)
        record = {
            'knot_id': '4_1',
            'braid_word': '1 2 -1'
        }
        parsed = parser.parse_record(record)
        assert parsed.braid_index == 3
        assert parsed.representation_source == 'braid_word'
        assert not parsed.tie_break_applied

    def test_extract_braid_index_from_dt_code(self, parser):
        """Test braid index extraction from DT code representation."""
        # DT code with 4 crossings (8 numbers)
        record = {
            'knot_id': '4_1',
            'dt_code': '4 6 8 2 4 6 8 2'
        }
        parsed = parser.parse_record(record)
        assert parsed.braid_index >= 2
        assert parsed.representation_source == 'dt_code'
        assert not parsed.tie_break_applied

    def test_extract_braid_index_tie_breaking(self, parser):
        """Test tie-breaking when both braid_word and dt_code present."""
        # Both representations present - braid_word should win
        record = {
            'knot_id': '5_2',
            'braid_word': '1 2 3 2 1',
            'dt_code': '6 8 10 2 4 6 8 10 2 4',
            'braid_index': 4  # Different value to test priority
        }
        parsed = parser.parse_record(record)
        # Braid word takes precedence
        assert parsed.representation_source == 'braid_word'
        assert parsed.tie_break_applied is True

    def test_extract_hyperbolic_volume(self, parser):
        """Test hyperbolic volume extraction with precision."""
        record = {
            'knot_id': '8_19',
            'hyperbolic_volume': 2.029883212819387
        }
        parsed = parser.parse_record(record)
        assert parsed.hyperbolic_volume is not None
        # Check precision (6 decimal places)
        assert parsed.hyperbolic_volume == round(2.029883212819387, 6)

    def test_extract_hyperbolic_volume_missing(self, parser):
        """Test handling of missing hyperbolic volume."""
        record = {'knot_id': '3_1'}  # No volume field
        parsed = parser.parse_record(record)
        assert parsed.hyperbolic_volume is None

    def test_extract_alternating_classification(self, parser):
        """Test alternating classification extraction."""
        # Boolean field
        record = {'knot_id': '3_1', 'is_alternating': True}
        parsed = parser.parse_record(record)
        assert parsed.is_alternating is True

        # String field - various formats
        record = {'knot_id': '3_1', 'alternating': 'true'}
        parsed = parser.parse_record(record)
        assert parsed.is_alternating is True

        record = {'knot_id': '3_1', 'alternating': 'non-alternating'}
        parsed = parser.parse_record(record)
        assert parsed.is_alternating is False

    def test_parse_multiple_records(self, parser):
        """Test parsing multiple records."""
        records = [
            {'knot_id': '3_1', 'crossing_number': 3, 'braid_word': '1 2 1'},
            {'knot_id': '4_1', 'crossing_number': 4, 'braid_word': '1 2 -1 2'},
            {'knot_id': '5_1', 'crossing_number': 5, 'braid_word': '1 2 3 4 1'}
        ]
        parsed = parser.parse_records(records)
        assert len(parsed) == 3
        assert all(isinstance(p, ParsedKnotData) for p in parsed)
        assert parsed[0].knot_id == '3_1'
        assert parsed[1].knot_id == '4_1'
        assert parsed[2].knot_id == '5_1'

    def test_braid_index_constraint(self, parser):
        """Verify braid_index <= crossing_number constraint."""
        record = {
            'knot_id': '4_1',
            'crossing_number': 4,
            'braid_word': '1 2 -1'
        }
        parsed = parser.parse_record(record)
        assert parsed.braid_index <= parsed.crossing_number

    def test_parse_with_all_fields(self, parser):
        """Test parsing record with all available fields."""
        record = {
            'knot_id': '8_19',
            'crossing_number': 8,
            'braid_word': '1 2 3 4 5 6 7',
            'hyperbolic_volume': 2.029883,
            'is_alternating': False,
            'dt_code': '8 10 12 14 16 2 4 6'
        }
        parsed = parser.parse_record(record)
        assert parsed.knot_id == '8_19'
        assert parsed.crossing_number == 8
        assert parsed.braid_index == 8  # 7 generators -> 8 strands
        assert parsed.hyperbolic_volume == 2.029883
        assert parsed.is_alternating is False
        assert parsed.representation_source == 'braid_word'


class TestParseKnotAtlasData:
    """Test cases for parse_knot_atlas_data convenience function."""

    def test_parse_and_return(self):
        """Test that function returns parsed data."""
        records = [
            {'knot_id': '3_1', 'crossing_number': 3, 'braid_word': '1 2 1'}
        ]
        result = parse_knot_atlas_data(records)
        assert len(result) == 1
        assert result[0].knot_id == '3_1'

    def test_parse_and_save(self, tmp_path):
        """Test that function saves to file when path provided."""
        records = [
            {'knot_id': '3_1', 'crossing_number': 3, 'braid_word': '1 2 1'}
        ]
        output_path = tmp_path / 'parsed.json'
        result = parse_knot_atlas_data(records, output_path)

        assert len(result) == 1
        assert output_path.exists()

        # Verify file content
        import json
        with open(output_path) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]['knot_id'] == '3_1'


class TestVerifyParserConsistency:
    """Test cases for verify_parser_consistency function."""

    def test_no_violations(self):
        """Test consistency check with valid data."""
        parsed = [
            ParsedKnotData(
                knot_id='3_1',
                crossing_number=3,
                braid_index=2,
                hyperbolic_volume=None,
                is_alternating=True,
                representation_source='braid_word',
                tie_break_applied=False
            ),
            ParsedKnotData(
                knot_id='4_1',
                crossing_number=4,
                braid_index=3,
                hyperbolic_volume=None,
                is_alternating=False,
                representation_source='braid_word',
                tie_break_applied=False
            )
        ]
        result = verify_parser_consistency(parsed)
        assert result['total_parsed'] == 2
        assert result['constraint_violations'] == 0

    def test_tie_break_counting(self):
        """Test that tie-breaks are counted correctly."""
        parsed = [
            ParsedKnotData(
                knot_id='3_1',
                crossing_number=3,
                braid_index=2,
                hyperbolic_volume=None,
                is_alternating=True,
                representation_source='braid_word',
                tie_break_applied=True
            ),
            ParsedKnotData(
                knot_id='4_1',
                crossing_number=4,
                braid_index=3,
                hyperbolic_volume=None,
                is_alternating=False,
                representation_source='braid_word',
                tie_break_applied=False
            )
        ]
        result = verify_parser_consistency(parsed)
        assert result['tie_breaks_applied'] == 1
        assert result['tie_break_percentage'] == 50.0

    def test_constraint_violation_detection(self):
        """Test detection of braid_index > crossing_number violations."""
        parsed = [
            ParsedKnotData(
                knot_id='3_1',
                crossing_number=3,
                braid_index=5,  # Invalid: braid_index > crossing_number
                hyperbolic_volume=None,
                is_alternating=True,
                representation_source='braid_word',
                tie_break_applied=False
            )
        ]
        result = verify_parser_consistency(parsed)
        assert result['constraint_violations'] == 1
        assert '3_1' in result['violations']
