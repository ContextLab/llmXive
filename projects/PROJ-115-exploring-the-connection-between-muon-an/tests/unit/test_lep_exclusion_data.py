"""
Unit tests for the LEP Exclusion Data schema.
"""
import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

from schemas.lep_exclusion_data import (
    LEPExclusionPoint,
    LEPExclusionData,
    validate_lep_schema
)


class TestLEPExclusionPoint:
    """Tests for the LEPExclusionPoint dataclass."""

    def test_create_point(self):
        """Test basic point creation."""
        point = LEPExclusionPoint(m_V=100.0, g=0.001)
        assert point.m_V == 100.0
        assert point.g == 0.001
        assert point.source == "LEP-II"
        assert point.comment is None

    def test_create_point_with_optional_fields(self):
        """Test point creation with optional fields."""
        point = LEPExclusionPoint(
            m_V=200.0,
            g=0.002,
            source="LEP-I",
            comment="Test comment"
        )
        assert point.source == "LEP-I"
        assert point.comment == "Test comment"

    def test_point_to_dict(self):
        """Test conversion to dictionary."""
        point = LEPExclusionPoint(m_V=150.0, g=0.0015, source="Test")
        d = point.to_dict()
        assert d['m_V'] == 150.0
        assert d['g'] == 0.0015
        assert d['source'] == "Test"

    def test_point_from_dict(self):
        """Test creation from dictionary."""
        data = {'m_V': 300.0, 'g': 0.003, 'source': 'Mock', 'comment': 'Note'}
        point = LEPExclusionPoint.from_dict(data)
        assert point.m_V == 300.0
        assert point.g == 0.003
        assert point.source == 'Mock'
        assert point.comment == 'Note'

    def test_validate_valid_point(self):
        """Test validation of a valid point."""
        point = LEPExclusionPoint(m_V=100.0, g=0.001)
        assert point.validate() is True

    def test_validate_invalid_mass(self):
        """Test validation with invalid mass (negative)."""
        point = LEPExclusionPoint(m_V=-100.0, g=0.001)
        assert point.validate() is False

    def test_validate_invalid_coupling(self):
        """Test validation with invalid coupling (zero)."""
        point = LEPExclusionPoint(m_V=100.0, g=0.0)
        assert point.validate() is False

    def test_validate_zero_mass(self):
        """Test validation with zero mass."""
        point = LEPExclusionPoint(m_V=0.0, g=0.001)
        assert point.validate() is False


class TestLEPExclusionData:
    """Tests for the LEPExclusionData container."""

    @pytest.fixture
    def sample_data(self):
        """Create a sample dataset for testing."""
        points = [
            LEPExclusionPoint(m_V=100.0, g=0.001),
            LEPExclusionPoint(m_V=200.0, g=0.002),
            LEPExclusionPoint(m_V=300.0, g=0.003)
        ]
        return LEPExclusionData(points=points, metadata={"test": True})

    def test_create_empty_data(self):
        """Test creation of empty dataset."""
        data = LEPExclusionData()
        assert len(data.points) == 0
        assert data.metadata == {}

    def test_add_point(self, sample_data):
        """Test adding a single point."""
        point = LEPExclusionPoint(m_V=400.0, g=0.004)
        sample_data.add_point(point)
        assert len(sample_data.points) == 4

    def test_add_points(self, sample_data):
        """Test adding multiple points."""
        new_points = [
            LEPExclusionPoint(m_V=500.0, g=0.005),
            LEPExclusionPoint(m_V=600.0, g=0.006)
        ]
        sample_data.add_points(new_points)
        assert len(sample_data.points) == 5

    def test_to_dataframe(self, sample_data):
        """Test conversion to pandas DataFrame."""
        df = sample_data.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert 'm_V' in df.columns
        assert 'g' in df.columns
        assert len(df) == 3

    def test_from_dataframe(self):
        """Test creation from DataFrame."""
        data = {
            'm_V': [100.0, 200.0, 300.0],
            'g': [0.001, 0.002, 0.003],
            'source': ['A', 'B', 'C']
        }
        df = pd.DataFrame(data)
        lep_data = LEPExclusionData.from_dataframe(df, metadata={"src": "test"})
        assert len(lep_data.points) == 3
        assert lep_data.points[0].source == 'A'

    def test_from_dataframe_missing_columns(self):
        """Test creation from DataFrame with missing columns raises error."""
        df = pd.DataFrame({'m_V': [100.0]})
        with pytest.raises(ValueError):
            LEPExclusionData.from_dataframe(df)

    def test_to_json_string(self, sample_data):
        """Test JSON serialization to string."""
        json_str = sample_data.to_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert 'points' in parsed
        assert 'metadata' in parsed

    def test_to_json_file(self, sample_data, tmp_path):
        """Test JSON serialization to file."""
        output_path = tmp_path / "test_lep.json"
        sample_data.to_json(output_path)
        assert output_path.exists()

        # Load and verify
        loaded = LEPExclusionData.from_json(output_path)
        assert len(loaded.points) == len(sample_data.points)

    def test_from_json(self, tmp_path):
        """Test loading from JSON file."""
        points = [LEPExclusionPoint(m_V=100.0, g=0.001)]
        data = LEPExclusionData(points=points, metadata={"key": "val"})
        output_path = tmp_path / "test.json"
        data.to_json(output_path)

        loaded = LEPExclusionData.from_json(output_path)
        assert len(loaded.points) == 1
        assert loaded.metadata["key"] == "val"

    def test_validate_all_valid(self, sample_data):
        """Test validation of all points in dataset."""
        assert sample_data.validate_all() is True

    def test_validate_all_invalid(self):
        """Test validation with an invalid point."""
        points = [
            LEPExclusionPoint(m_V=100.0, g=0.001),
            LEPExclusionPoint(m_V=-50.0, g=0.001)  # Invalid
        ]
        data = LEPExclusionData(points=points)
        assert data.validate_all() is False


class TestValidateLEPSchema:
    """Tests for the validate_lep_schema function."""

    def test_valid_dataset(self):
        """Test validation of a valid dataset."""
        points = [LEPExclusionPoint(m_V=100.0, g=0.001)]
        data = LEPExclusionData(points=points)
        result = validate_lep_schema(data)
        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_invalid_dataset(self):
        """Test validation of an invalid dataset."""
        points = [
            LEPExclusionPoint(m_V=100.0, g=0.001),
            LEPExclusionPoint(m_V=-100.0, g=0.001)
        ]
        data = LEPExclusionData(points=points)
        result = validate_lep_schema(data)
        assert result['valid'] is False
        assert len(result['errors']) > 0

    def test_empty_dataset(self):
        """Test validation of an empty dataset."""
        data = LEPExclusionData()
        result = validate_lep_schema(data)
        assert result['valid'] is True  # Empty is technically valid
        assert len(result['warnings']) > 0

    def test_point_count_in_result(self):
        """Test that point count is included in validation result."""
        points = [LEPExclusionPoint(m_V=100.0, g=0.001) for _ in range(5)]
        data = LEPExclusionData(points=points)
        result = validate_lep_schema(data)
        assert result['point_count'] == 5