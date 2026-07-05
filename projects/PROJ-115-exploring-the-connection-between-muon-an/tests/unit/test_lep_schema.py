"""
Unit tests for the LEP_Exclusion_Data schema.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from schemas.lep_exclusion_data import (
    LEPExclusionPoint, 
    LEPExclusionData, 
    validate_lep_schema
)

def test_lep_exclusion_point_creation():
    """Test creation of a single LEP exclusion point."""
    point = LEPExclusionPoint(
        m_V=100.0,
        m_chi=50.0,
        g_limit=0.01,
        source="Test Source"
    )
    assert point.m_V == 100.0
    assert point.m_chi == 50.0
    assert point.g_limit == 0.01
    assert point.source == "Test Source"
    assert point.notes is None

def test_lep_exclusion_point_to_dict():
    """Test serialization of a point."""
    point = LEPExclusionPoint(m_V=10.0, m_chi=5.0, g_limit=0.1)
    d = point.to_dict()
    assert d['m_V'] == 10.0
    assert d['m_chi'] == 5.0
    assert d['g_limit'] == 0.1

def test_lep_exclusion_data_validation_positive():
    """Test validation with valid data."""
    points = [
        LEPExclusionPoint(m_V=10.0, m_chi=5.0, g_limit=0.1),
        LEPExclusionPoint(m_V=20.0, m_chi=10.0, g_limit=0.05)
    ]
    data = LEPExclusionData(points=points, metadata={"source": "Test"})
    assert data.validate() is True
    assert validate_lep_schema(data) is True

def test_lep_exclusion_data_validation_negative():
    """Test validation with invalid data (negative mass)."""
    points = [
        LEPExclusionPoint(m_V=-10.0, m_chi=5.0, g_limit=0.1)
    ]
    data = LEPExclusionData(points=points, metadata={})
    assert data.validate() is False

def test_lep_exclusion_data_to_dataframe():
    """Test conversion to DataFrame."""
    points = [
        LEPExclusionPoint(m_V=10.0, m_chi=5.0, g_limit=0.1),
        LEPExclusionPoint(m_V=20.0, m_chi=10.0, g_limit=0.05)
    ]
    data = LEPExclusionData(points=points, metadata={})
    df = data.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert 'm_V' in df.columns
    assert 'g_limit' in df.columns

def test_lep_exclusion_data_roundtrip():
    """Test saving to parquet and loading back."""
    points = [
        LEPExclusionPoint(m_V=100.0, m_chi=50.0, g_limit=0.01),
        LEPExclusionPoint(m_V=200.0, m_chi=100.0, g_limit=0.02)
    ]
    original = LEPExclusionData(points=points, metadata={"test": True})
    
    # Save to temp file
    temp_path = Path("tests/temp_test_lep.parquet")
    temp_path.parent.mkdir(exist_ok=True)
    original.to_parquet(str(temp_path))
    
    # Load back
    loaded = LEPExclusionData.from_parquet(str(temp_path))
    
    assert len(loaded.points) == len(original.points)
    assert abs(loaded.points[0].m_V - original.points[0].m_V) < 1e-6
    assert abs(loaded.points[0].g_limit - original.points[0].g_limit) < 1e-6
    
    # Cleanup
    temp_path.unlink()
    
def test_get_limit_for_mass():
    """Test retrieval of limit for specific mass."""
    points = [
        LEPExclusionPoint(m_V=100.0, m_chi=50.0, g_limit=0.01)
    ]
    data = LEPExclusionData(points=points, metadata={})
    
    limit = data.get_limit_for_mass(100.0, 50.0)
    assert limit == 0.01
    
    limit_miss = data.get_limit_for_mass(100.0, 51.0, tolerance=0.5)
    assert limit_miss is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])