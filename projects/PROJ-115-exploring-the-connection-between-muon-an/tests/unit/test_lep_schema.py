"""
Unit tests for the LEP Exclusion Data schema.

Tests cover:
- Data class instantiation and validation
- Schema validation logic
- Serialization/deserialization
- Edge cases and error handling
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import tempfile

from schemas.lep_exclusion_data import (
    LEPExclusionPoint, 
    LEPExclusionData, 
    validate_lep_schema
)


class TestLEPExclusionPoint:
    """Tests for LEPExclusionPoint dataclass."""
    
    def test_valid_point_creation(self):
        """Test creation of a valid exclusion point."""
        point = LEPExclusionPoint(
            mass_mev=100.0,
            coupling_g=1e-3,
            limit_type="95% CL",
            source="ALEPH"
        )
        
        assert point.mass_mev == 100.0
        assert point.coupling_g == 1e-3
        assert point.limit_type == "95% CL"
        assert point.source == "ALEPH"
        assert point.notes is None
        
    def test_default_values(self):
        """Test default values for optional fields."""
        point = LEPExclusionPoint(mass_mev=50.0, coupling_g=5e-4)
        
        assert point.limit_type == "95% CL"
        assert point.source == "LEP Combined"
        assert point.notes is None
        
    def test_negative_mass_raises_error(self):
        """Test that negative mass raises ValueError."""
        with pytest.raises(ValueError, match="mass_mev must be positive"):
            LEPExclusionPoint(mass_mev=-10.0, coupling_g=1e-3)
            
    def test_zero_mass_raises_error(self):
        """Test that zero mass raises ValueError."""
        with pytest.raises(ValueError, match="mass_mev must be positive"):
            LEPExclusionPoint(mass_mev=0.0, coupling_g=1e-3)
            
    def test_negative_coupling_raises_error(self):
        """Test that negative coupling raises ValueError."""
        with pytest.raises(ValueError, match="coupling_g must be positive"):
            LEPExclusionPoint(mass_mev=100.0, coupling_g=-1e-3)
            
    def test_zero_coupling_raises_error(self):
        """Test that zero coupling raises ValueError."""
        with pytest.raises(ValueError, match="coupling_g must be positive"):
            LEPExclusionPoint(mass_mev=100.0, coupling_g=0.0)
            
    def test_to_dict(self):
        """Test dictionary conversion."""
        point = LEPExclusionPoint(
            mass_mev=200.0,
            coupling_g=2e-3,
            limit_type="95% CL",
            source="DELPHI",
            notes="Test note"
        )
        
        d = point.to_dict()
        assert d["mass_mev"] == 200.0
        assert d["coupling_g"] == 2e-3
        assert d["limit_type"] == "95% CL"
        assert d["source"] == "DELPHI"
        assert d["notes"] == "Test note"
        
    def test_from_dict(self):
        """Test dictionary reconstruction."""
        d = {
            "mass_mev": 150.0,
            "coupling_g": 1.5e-3,
            "limit_type": "95% CL",
            "source": "L3",
            "notes": "Reconstructed"
        }
        
        point = LEPExclusionPoint.from_dict(d)
        assert point.mass_mev == 150.0
        assert point.coupling_g == 1.5e-3
        assert point.limit_type == "95% CL"
        assert point.source == "L3"
        assert point.notes == "Reconstructed"
        
    def test_from_dict_missing_optional_fields(self):
        """Test reconstruction with missing optional fields."""
        d = {
            "mass_mev": 150.0,
            "coupling_g": 1.5e-3
        }
        
        point = LEPExclusionPoint.from_dict(d)
        assert point.limit_type == "95% CL"
        assert point.source == "LEP Combined"
        assert point.notes is None


class TestLEPExclusionData:
    """Tests for LEPExclusionData container."""
    
    @pytest.fixture
    def sample_points(self):
        """Create sample exclusion points."""
        return [
            LEPExclusionPoint(mass_mev=10.0, coupling_g=1e-2),
            LEPExclusionPoint(mass_mev=50.0, coupling_g=5e-3),
            LEPExclusionPoint(mass_mev=100.0, coupling_g=1e-3),
            LEPExclusionPoint(mass_mev=500.0, coupling_g=5e-3),
        ]
        
    def test_empty_data_default_metadata(self, sample_points):
        """Test that empty data gets default metadata."""
        data = LEPExclusionData(points=sample_points)
        
        assert "source" in data.metadata
        assert "reference" in data.metadata
        assert data.metadata["version"] == "1.0"
        
    def test_add_point(self, sample_points):
        """Test adding a single point."""
        data = LEPExclusionData()
        point = LEPExclusionPoint(mass_mev=200.0, coupling_g=2e-3)
        
        data.add_point(point)
        assert len(data.points) == 1
        assert data.points[0].mass_mev == 200.0
        
    def test_add_points(self, sample_points):
        """Test adding multiple points."""
        data = LEPExclusionData()
        data.add_points(sample_points)
        
        assert len(data.points) == len(sample_points)
        
    def test_get_min_max_mass(self, sample_points):
        """Test min/max mass retrieval."""
        data = LEPExclusionData(points=sample_points)
        
        assert data.get_min_mass() == 10.0
        assert data.get_max_mass() == 500.0
        
    def test_get_min_max_mass_empty(self):
        """Test min/max mass with empty data."""
        data = LEPExclusionData()
        
        assert data.get_min_mass() is None
        assert data.get_max_mass() is None
        
    def test_get_min_coupling(self, sample_points):
        """Test minimum coupling retrieval."""
        data = LEPExclusionData(points=sample_points)
        
        assert data.get_min_coupling() == 1e-3
        
    def test_to_dataframe(self, sample_points):
        """Test DataFrame conversion."""
        data = LEPExclusionData(points=sample_points)
        df = data.to_dataframe()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(sample_points)
        assert "mass_mev" in df.columns
        assert "coupling_g" in df.columns
        
    def test_to_json(self, sample_points):
        """Test JSON serialization."""
        data = LEPExclusionData(points=sample_points)
        json_str = data.to_json()
        
        assert isinstance(json_str, str)
        assert "points" in json_str
        assert "metadata" in json_str
        
    def test_to_json_file(self, sample_points):
        """Test JSON file writing."""
        data = LEPExclusionData(points=sample_points)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            data.to_json(temp_path)
            assert temp_path.exists()
            
            # Verify content
            with open(temp_path, 'r') as f:
                loaded = json.load(f)
            assert len(loaded["points"]) == len(sample_points)
        finally:
            if temp_path.exists():
                temp_path.unlink()
                
    def test_from_json(self, sample_points):
        """Test JSON loading."""
        data = LEPExclusionData(points=sample_points)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            data.to_json(temp_path)
            loaded = LEPExclusionData.from_json(temp_path)
            
            assert len(loaded.points) == len(sample_points)
            assert loaded.points[0].mass_mev == sample_points[0].mass_mev
        finally:
            if temp_path.exists():
                temp_path.unlink()
                
    def test_to_parquet(self, sample_points):
        """Test Parquet file writing."""
        data = LEPExclusionData(points=sample_points)
        
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            data.to_parquet(temp_path)
            assert temp_path.exists()
            
            # Verify content
            loaded = LEPExclusionData.from_parquet(temp_path)
            assert len(loaded.points) == len(sample_points)
        finally:
            if temp_path.exists():
                temp_path.unlink()
                
    def test_from_parquet(self, sample_points):
        """Test Parquet file loading."""
        data = LEPExclusionData(points=sample_points)
        
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            data.to_parquet(temp_path)
            loaded = LEPExclusionData.from_parquet(temp_path)
            
            assert len(loaded.points) == len(sample_points)
            assert np.isclose(loaded.points[0].coupling_g, sample_points[0].coupling_g)
        finally:
            if temp_path.exists():
                temp_path.unlink()

class TestValidateLEPSchema:
    """Tests for schema validation logic."""
    
    def test_valid_data_passes(self):
        """Test that valid data passes validation."""
        points = [
            LEPExclusionPoint(mass_mev=10.0, coupling_g=1e-2),
            LEPExclusionPoint(mass_mev=50.0, coupling_g=5e-3),
            LEPExclusionPoint(mass_mev=100.0, coupling_g=1e-3),
        ]
        data = LEPExclusionData(points=points)
        
        assert validate_lep_schema(data) is True
        
    def test_empty_points_raises_error(self):
        """Test that empty points list raises ValueError."""
        data = LEPExclusionData(points=[])
        
        with pytest.raises(ValueError, match="must contain at least one point"):
            validate_lep_schema(data)
            
    def test_unsorted_mass_raises_error(self):
        """Test that unsorted mass values raise ValueError."""
        points = [
            LEPExclusionPoint(mass_mev=100.0, coupling_g=1e-3),
            LEPExclusionPoint(mass_mev=50.0, coupling_g=5e-3),  # Out of order
            LEPExclusionPoint(mass_mev=200.0, coupling_g=2e-3),
        ]
        data = LEPExclusionData(points=points)
        
        with pytest.raises(ValueError, match="not sorted by mass"):
            validate_lep_schema(data)
            
    def test_duplicate_point_raises_error(self):
        """Test that duplicate points raise ValueError."""
        points = [
            LEPExclusionPoint(mass_mev=50.0, coupling_g=5e-3),
            LEPExclusionPoint(mass_mev=50.0, coupling_g=5e-3),  # Duplicate
            LEPExclusionPoint(mass_mev=100.0, coupling_g=1e-3),
        ]
        data = LEPExclusionData(points=points)
        
        with pytest.raises(ValueError, match="Duplicate point"):
            validate_lep_schema(data)
            
    def test_missing_metadata_raises_error(self):
        """Test that missing metadata raises ValueError."""
        points = [LEPExclusionPoint(mass_mev=50.0, coupling_g=5e-3)]
        data = LEPExclusionData(points=points, metadata={})
        
        with pytest.raises(ValueError, match="Missing required metadata"):
            validate_lep_schema(data)
            
    def test_invalid_point_in_list_raises_error(self):
        """Test that invalid point in list raises ValueError."""
        # Create a valid data object, then manually inject an invalid point
        points = [
            LEPExclusionPoint(mass_mev=50.0, coupling_g=5e-3),
            LEPExclusionPoint(mass_mev=100.0, coupling_g=1e-3),
        ]
        data = LEPExclusionData(points=points)
        
        # Manually add an invalid point (bypassing constructor)
        invalid_point = LEPExclusionPoint(mass_mev=50.0, coupling_g=5e-3)
        invalid_point.mass_mev = -10.0  # Invalid
        data.points.append(invalid_point)
        
        with pytest.raises(ValueError):
            validate_lep_schema(data)
