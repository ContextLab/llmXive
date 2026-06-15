"""
Unit tests for data quantities documentation generator.
"""
import pytest
from pathlib import Path
import tempfile
import json
from analysis.data_quantities import (
    load_cleaned_knots_data,
    calculate_null_percentages_per_field,
    generate_data_quantities_report,
    write_data_quantities_report_md
)

class TestDataQuantities:
    """Test suite for data quantities generation."""

    def test_calculate_null_percentages_empty_list(self):
        """Test null percentage calculation with empty knot list."""
        knots = []
        fields = ['knot_id', 'crossing_number']
        result = calculate_null_percentages_per_field(knots, fields)
        
        assert result == {'knot_id': 0.0, 'crossing_number': 0.0}

    def test_calculate_null_percentages_no_nulls(self):
        """Test null percentage calculation with no null values."""
        knots = [
            {'knot_id': '3_1', 'crossing_number': '3'},
            {'knot_id': '4_1', 'crossing_number': '4'},
            {'knot_id': '5_1', 'crossing_number': '5'}
        ]
        fields = ['knot_id', 'crossing_number']
        result = calculate_null_percentages_per_field(knots, fields)
        
        assert result['knot_id'] == 0.0
        assert result['crossing_number'] == 0.0

    def test_calculate_null_percentages_with_nulls(self):
        """Test null percentage calculation with null values."""
        knots = [
            {'knot_id': '3_1', 'crossing_number': '3'},
            {'knot_id': '', 'crossing_number': '4'},
            {'knot_id': '5_1', 'crossing_number': ''}
        ]
        fields = ['knot_id', 'crossing_number']
        result = calculate_null_percentages_per_field(knots, fields)
        
        assert result['knot_id'] == 33.33
        assert result['crossing_number'] == 33.33

    def test_generate_data_quantities_report_basic(self):
        """Test basic report generation."""
        knots = [
            {'knot_id': '3_1', 'crossing_number': '3'},
            {'knot_id': '4_1', 'crossing_number': '4'}
        ]
        counts_per_crossing = {3: 1, 4: 1}
        null_percentages = {'knot_id': 0.0, 'crossing_number': 0.0}
        
        report = generate_data_quantities_report(
            knots=knots,
            counts_per_crossing=counts_per_crossing,
            null_percentages=null_percentages,
            total_records=2,
            hyperbolic_count=2,
            excluded_count=0
        )
        
        assert report['total_records'] == 2
        assert report['hyperbolic_knots'] == 2
        assert report['excluded_knots'] == 0
        assert '3' in report['knots_per_crossing_number']
        assert report['crossing_number_range']['min'] == 3
        assert report['crossing_number_range']['max'] == 4

    def test_write_data_quantities_report_md(self):
        """Test markdown report writing."""
        report = {
            'generated_at': '2026-01-15T10:30:00.000000',
            'total_records': 10,
            'knots_per_crossing_number': {'3': 1, '4': 2, '5': 3},
            'null_percentages': {'knot_id': 0.0, 'crossing_number': 5.0},
            'hyperbolic_knots': 8,
            'excluded_knots': 2,
            'crossing_number_range': {'min': 3, 'max': 5}
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_report.md'
            write_data_quantities_report_md(report, output_path)
            
            assert output_path.exists()
            content = output_path.read_text()
            
            assert '# Data Quantities Report' in content
            assert 'Total Records: 10' in content
            assert 'Hyperbolic Knots: 8' in content
            assert 'Excluded Knots: 2' in content
            assert '| 3 | 1 |' in content
            assert '| 4 | 2 |' in content
            assert '| 5 | 3 |' in content
            assert 'knot_id' in content
            assert 'crossing_number' in content
            assert '5.00%' in content