"""
Unit tests for the download module, specifically T011b logic.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.src.data.download import verify_bmrq_column, generate_data_gap_report

def test_verify_bmrq_column_present():
    """Test that verification passes when BMRQ column is present."""
    df = pd.DataFrame({
        "BMRQ_Total": [10, 20, 30],
        "age": [20, 21, 22]
    })
    is_valid, missing = verify_bmrq_column(df, ["BMRQ_Total"])
    assert is_valid is True
    assert missing == []

def test_verify_bmrq_column_missing():
    """Test that verification fails when BMRQ column is missing."""
    df = pd.DataFrame({
        "age": [20, 21, 22],
        "sex": ["M", "F", "M"]
    })
    is_valid, missing = verify_bmrq_column(df, ["BMRQ_Total"])
    assert is_valid is False
    assert missing == ["BMRQ_Total"]

def test_verify_multiple_missing_columns():
    """Test that multiple missing columns are reported."""
    df = pd.DataFrame({
        "age": [20, 21, 22]
    })
    required = ["BMRQ_Total", "BMRQ_Emotion"]
    is_valid, missing = verify_bmrq_column(df, required)
    assert is_valid is False
    assert set(missing) == set(required)

def test_generate_data_gap_report(tmp_path):
    """Test that the data gap report is generated correctly."""
    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    output_path = output_dir / "data_gap_report.md"
    
    missing_cols = ["BMRQ_Total", "BMRQ_Emotion"]
    dataset_id = "ds000233"
    
    generate_data_gap_report(missing_cols, dataset_id, output_path)
    
    assert output_path.exists()
    
    content = output_path.read_text()
    assert "Data Gap Report" in content
    assert "ds000233" in content
    assert "BMRQ_Total" in content
    assert "BMRQ_Emotion" in content
    assert "Action Required" in content

def test_generate_data_gap_report_content(tmp_path):
    """Test the content of the generated data gap report."""
    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    output_path = output_dir / "data_gap_report.md"
    
    missing_cols = ["BMRQ_Total"]
    dataset_id = "ds001234"
    
    generate_data_gap_report(missing_cols, dataset_id, output_path)
    
    content = output_path.read_text()
    assert f"- `{missing_cols[0]}`" in content
    assert f"Dataset ID**: {dataset_id}" in content
    assert "CRITICAL" in content