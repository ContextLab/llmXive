"""
Integration test for T024: Timing profile generation.
"""
import os
import sys
import tempfile
import json
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.evaluate import (
    calculate_inference_time_projection,
    generate_timing_profile,
    load_scaling_profile
)
from src.utils import write_json

@pytest.fixture
def temp_profiling_data(tmp_path):
    """Create temporary profiling data for testing."""
    profiling_logs = {
        "clip_001": {"cpu_time_seconds": 0.5, "memory_mb": 100},
        "clip_002": {"cpu_time_seconds": 0.6, "memory_mb": 105},
        "clip_003": {"cpu_time_seconds": 0.55, "memory_mb": 102},
        "clip_004": {"cpu_time_seconds": 0.45, "memory_mb": 98},
        "clip_005": {"cpu_time_seconds": 0.52, "memory_mb": 101},
    }
    
    profiling_path = tmp_path / "profiling_logs.json"
    write_json(profiling_logs, str(profiling_path))
    return str(profiling_path)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    return tmp_path

def test_calculate_inference_time_projection(temp_profiling_data):
    """Test inference time projection calculation."""
    scaling_profile = load_scaling_profile(temp_profiling_data)
    
    avg_time, projected_hours = calculate_inference_time_projection(
        scaling_profile, n_clips=10000
    )
    
    # Verify calculations
    assert avg_time > 0, "Average time per clip must be positive"
    assert projected_hours > 0, "Projected hours must be positive"
    
    # Expected average: (0.5 + 0.6 + 0.55 + 0.45 + 0.52) / 5 = 0.524
    expected_avg = 0.524
    assert abs(avg_time - expected_avg) < 0.001, f"Expected ~{expected_avg}, got {avg_time}"
    
    # Expected total seconds: 0.524 * 10000 = 5240
    # Expected hours: 5240 / 3600 = 1.455...
    expected_hours = 5240 / 3600
    assert abs(projected_hours - expected_hours) < 0.01, f"Expected ~{expected_hours}, got {projected_hours}"

def test_generate_timing_profile_creates_csv(temp_profiling_data, temp_output_dir):
    """Test that generate_timing_profile creates the CSV file."""
    output_csv = temp_output_dir / "timing_profile.csv"
    
    results = generate_timing_profile(
        n_clips=10000,
        scaling_profile_path=temp_profiling_data,
        output_path=str(output_csv)
    )
    
    # Verify file exists
    assert output_csv.exists(), "timing_profile.csv was not created"
    
    # Verify content
    df = pd.read_csv(str(output_csv))
    assert not df.empty, "timing_profile.csv is empty"
    assert "projected_total_hours" in df.columns, "Missing projected_total_hours column"
    assert "avg_time_per_clip_seconds" in df.columns, "Missing avg_time_per_clip_seconds column"
    
    # Verify values match calculation
    assert abs(df["projected_total_hours"].iloc[0] - 1.455) < 0.01, "Incorrect projected hours"

def test_generate_timing_profile_empty_profile_raises(temp_output_dir):
    """Test that empty scaling profile raises an error."""
    # Create empty profiling file
    empty_profile = temp_output_dir / "empty_profiling.json"
    write_json([], str(empty_profile))
    
    with pytest.raises(ValueError, match="Scaling profile is empty"):
        generate_timing_profile(
            scaling_profile_path=str(empty_profile),
            output_path=str(temp_output_dir / "output.csv")
        )

def test_generate_timing_profile_missing_file_raises(temp_output_dir):
    """Test that missing profiling file raises an error."""
    with pytest.raises(FileNotFoundError, match="Scaling profile not found"):
        generate_timing_profile(
            scaling_profile_path=str(temp_output_dir / "nonexistent.json"),
            output_path=str(temp_output_dir / "output.csv")
        )