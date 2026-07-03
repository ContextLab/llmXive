import pytest
import tempfile
import os
from datetime import datetime
import pandas as pd

# Add code to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.ingestion import (
    parse_ilrs_normal_point_line,
    parse_slr_file,
    normal_points_to_dataframe,
    NormalPoint
)


def test_parse_valid_line():
    """Test parsing a standard ILRS normal point line."""
    # Format: YYYY MM DD HH MM SS.SSSS RANGE RR RES SIG STA
    line = "2023 01 15 12 30 45.1234 7500000.50 0.01 0.005 1.0e-3 7840"
    result = parse_ilrs_normal_point_line(line, "LAGEOS-1")
    
    assert result is not None
    assert result.satellite_id == "LAGEOS-1"
    assert result.epoch.year == 2023
    assert result.epoch.month == 1
    assert result.epoch.day == 15
    assert result.epoch.hour == 12
    assert result.epoch.minute == 30
    assert abs(result.range_m - 7500000.50) < 1e-5
    assert result.range_rate == 0.01
    assert result.residual_m == 0.005
    assert result.sigma_m == 1.0e-3
    assert result.station_id == "7840"


def test_parse_line_with_comments():
    """Test that comment lines are skipped."""
    assert parse_ilrs_normal_point_line("# This is a comment", "SAT") is None
    assert parse_ilrs_normal_point_line("! Another comment", "SAT") is None
    assert parse_ilrs_normal_point_line("", "SAT") is None


def test_parse_line_short():
    """Test that lines with insufficient data are skipped."""
    assert parse_ilrs_normal_point_line("2023 01 15", "SAT") is None


def test_parse_slr_file_integration():
    """Test full file parsing workflow."""
    # Create a temporary file with mock data
    mock_content = """# Mock SLR Data
    2023 06 01 10 00 00.0000 7500000.00 0.00 0.001 1.0e-3 7840
    2023 06 01 10 01 00.0000 7500001.00 0.00 0.002 1.0e-3 7841
    # Comment line
    2023 06 01 10 02 00.0000 7500002.00 0.00 0.003 1.0e-3 7840
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(mock_content)
        temp_path = f.name
    
    try:
        points = parse_slr_file(temp_path, "TEST-SAT")
        
        assert len(points) == 3
        assert points[0].epoch.day == 1
        assert points[1].epoch.day == 1
        assert points[2].epoch.day == 1
    finally:
        os.unlink(temp_path)


def test_normal_points_to_dataframe():
    """Test conversion of NormalPoint list to DataFrame."""
    points = [
        NormalPoint("SAT1", datetime(2023, 1, 1, 12, 0, 0), 7000000.0),
        NormalPoint("SAT1", datetime(2023, 1, 1, 12, 1, 0), 7000001.0),
    ]
    
    df = normal_points_to_dataframe(points)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert 'epoch' in df.columns
    assert 'range_m' in df.columns
    assert df['satellite_id'].iloc[0] == "SAT1"
    assert pd.api.types.is_datetime64_any_dtype(df['epoch'])


def test_empty_list_to_dataframe():
    """Test conversion of empty list."""
    df = normal_points_to_dataframe([])
    assert df.empty