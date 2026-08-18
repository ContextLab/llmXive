import pytest
import json
from pathlib import Path
import tempfile
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from download import count_unique_planets, validate_sample_size

class TestCountUniquePlanets:
    """Test cases for count_unique_planets function."""

    def test_empty_metadata(self):
        """Test counting with empty metadata list."""
        result = count_unique_planets([])
        assert result == 0

    def test_single_planet(self):
        """Test counting with single planet."""
        metadata = [
            {'planet_name': 'HD 209458 b'}
        ]
        result = count_unique_planets(metadata)
        assert result == 1

    def test_multiple_unique_planets(self):
        """Test counting with multiple unique planets."""
        metadata = [
            {'planet_name': 'HD 209458 b'},
            {'planet_name': 'WASP-12 b'},
            {'planet_name': 'WASP-17 b'}
        ]
        result = count_unique_planets(metadata)
        assert result == 3

    def test_duplicate_planets(self):
        """Test that duplicates are not counted."""
        metadata = [
            {'planet_name': 'HD 209458 b'},
            {'planet_name': 'HD 209458 b'},
            {'planet_name': 'WASP-12 b'}
        ]
        result = count_unique_planets(metadata)
        assert result == 2

    def test_missing_planet_name(self):
        """Test handling of records with missing planet_name."""
        metadata = [
            {'planet_name': 'HD 209458 b'},
            {},  # Missing planet_name
            {'planet_name': 'WASP-12 b'}
        ]
        result = count_unique_planets(metadata)
        assert result == 2

    def test_none_planet_name(self):
        """Test handling of records with None planet_name."""
        metadata = [
            {'planet_name': 'HD 209458 b'},
            {'planet_name': None},
            {'planet_name': 'WASP-12 b'}
        ]
        result = count_unique_planets(metadata)
        assert result == 2

class TestValidateSampleSize:
    """Test cases for validate_sample_size function."""

    def test_within_range(self):
        """Test validation with count in target range."""
        report = validate_sample_size(35)
        assert report['count'] == 35
        assert report['validation_status'] == 'proceed'

    def test_below_range(self):
        """Test validation with count below target range."""
        report = validate_sample_size(25)
        assert report['count'] == 25
        assert report['validation_status'] == 'proceed'

    def test_above_range(self):
        """Test validation with count above target range."""
        report = validate_sample_size(50)
        assert report['count'] == 50
        assert report['validation_status'] == 'proceed'

    def test_boundary_low(self):
        """Test validation at lower boundary."""
        report = validate_sample_size(30)
        assert report['count'] == 30
        assert report['validation_status'] == 'proceed'

    def test_boundary_high(self):
        """Test validation at upper boundary."""
        report = validate_sample_size(45)
        assert report['count'] == 45
        assert report['validation_status'] == 'proceed'

    def test_report_structure(self):
        """Test that report has correct structure."""
        report = validate_sample_size(35)
        assert 'count' in report
        assert 'validation_status' in report
        assert isinstance(report['count'], int)
        assert isinstance(report['validation_status'], str)
