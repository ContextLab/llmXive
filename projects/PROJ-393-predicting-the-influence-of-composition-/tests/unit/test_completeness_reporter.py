import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import json
import sys

# Add code to path if running directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.preprocessing.completeness_reporter import calculate_source_proportions, generate_completeness_report, run_completeness_report_pipeline

@pytest.fixture
def sample_df():
    """Create a sample dataframe with various source types and nulls."""
    data = {
        "composition": ["Co2MnGa", "Fe3Al", "Ni2MnGa", "CoFeCr", "Mn3Ga"],
        "source_type": ["NIST", "NIST", "Journal", "Manual", "NIST"],
        "coercivity_oe": [10.0, 20.0, None, 5.0, 15.0],
        "saturation_magnetization_emu_g": [100.0, 200.0, 150.0, 80.0, None],
        "remanence_emu_g": [50.0, 100.0, 75.0, 40.0, 60.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path

def test_calculate_source_proportions_valid_data(sample_df):
    """Test that proportions are calculated correctly for valid data."""
    result = calculate_source_proportions(sample_df)
    
    # NIST: 3 rows total. Row 1 (10, 100, 50) valid. Row 2 (20, 200, 100) valid. Row 5 (15, None, 60) invalid (saturation null).
    # NIST: 2 valid, 3 total.
    assert result["sources"]["NIST"]["total_rows"] == 3
    assert result["sources"]["NIST"]["valid_rows"] == 2
    assert result["sources"]["NIST"]["completeness_pct"] == pytest.approx(66.67, rel=0.1)
    
    # Journal: 1 row total. Row 3 (None, 150, 75) invalid (coercivity null).
    assert result["sources"]["Journal"]["total_rows"] == 1
    assert result["sources"]["Journal"]["valid_rows"] == 0
    assert result["sources"]["Journal"]["completeness_pct"] == 0.0
    
    # Manual: 1 row total. Row 4 (5, 80, 40) valid.
    assert result["sources"]["Manual"]["total_rows"] == 1
    assert result["sources"]["Manual"]["valid_rows"] == 1
    assert result["sources"]["Manual"]["completeness_pct"] == 100.0
    
    # Overall: 5 total, 3 valid (NIST 2 + Manual 1).
    assert result["overall"]["total_rows"] == 5
    assert result["overall"]["valid_rows"] == 3
    assert result["overall"]["completeness_pct"] == pytest.approx(60.0, rel=0.1)

def test_generate_completeness_report_writes_file(sample_df, temp_output_dir):
    """Test that the report is written to a JSON file."""
    output_path = temp_output_dir / "test_report.json"
    proportions = calculate_source_proportions(sample_df)
    generate_completeness_report(proportions, output_path)
    
    assert output_path.exists()
    with open(output_path, "r") as f:
        loaded = json.load(f)
    
    assert "sources" in loaded
    assert "overall" in loaded
    assert "NIST" in loaded["sources"]
    assert "Journal" in loaded["sources"]
    assert "Manual" in loaded["sources"]

def test_empty_dataframe():
    """Test behavior with an empty dataframe."""
    df = pd.DataFrame(columns=["composition", "source_type", "coercivity_oe", "saturation_magnetization_emu_g", "remanence_emu_g"])
    result = calculate_source_proportions(df)
    
    assert result["overall"]["total_rows"] == 0
    assert result["overall"]["valid_rows"] == 0
    assert result["overall"]["completeness_pct"] == 0.0
    for src in ["NIST", "Journal", "Manual"]:
        assert result["sources"][src]["total_rows"] == 0
        assert result["sources"][src]["valid_rows"] == 0
        assert result["sources"][src]["completeness_pct"] == 0.0

def test_missing_source_type_column():
    """Test behavior when source_type column is missing (defaults to Manual)."""
    data = {
        "composition": ["Co2MnGa"],
        "coercivity_oe": [10.0],
        "saturation_magnetization_emu_g": [100.0],
        "remanence_emu_g": [50.0]
    }
    df = pd.DataFrame(data)
    result = calculate_source_proportions(df)
    
    # All rows should be counted as Manual
    assert result["sources"]["Manual"]["total_rows"] == 1
    assert result["sources"]["Manual"]["valid_rows"] == 1
    assert result["sources"]["NIST"]["total_rows"] == 0
    assert result["sources"]["Journal"]["total_rows"] == 0

def test_run_completeness_report_pipeline(tmp_path):
    """Test the full pipeline with a temporary file."""
    # Create input file
    input_dir = tmp_path / "data" / "processed"
    input_dir.mkdir(parents=True)
    input_path = input_dir / "alloys_raw.csv"
    
    data = {
        "composition": ["Co2MnGa"],
        "source_type": ["NIST"],
        "coercivity_oe": [10.0],
        "saturation_magnetization_emu_g": [100.0],
        "remanence_emu_g": [50.0]
    }
    df = pd.DataFrame(data)
    df.to_csv(input_path, index=False)
    
    output_path = tmp_path / "data" / "processed" / "completeness_report.json"
    
    run_completeness_report_pipeline(input_path, output_path)
    
    assert output_path.exists()
    with open(output_path, "r") as f:
        report = json.load(f)
    
    assert report["sources"]["NIST"]["valid_rows"] == 1
    assert report["overall"]["completeness_pct"] == 100.0