"""
Unit tests for additional_completeness.py
"""
from __future__ import annotations

import csv
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from code.data.additional_completeness import (
    analyze_completeness,
    load_knot_data,
    write_report,
    CompletenessStats,
    CompletenessReport
)


def test_load_knot_data_empty_file():
    """Test loading an empty CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("id,arc_index,seifert_circle_count,bridge_number\n")
        temp_path = Path(f.name)
    
    try:
        records = load_knot_data(temp_path)
        assert len(records) == 0
    finally:
        temp_path.unlink()


def test_load_knot_data_with_data():
    """Test loading a CSV file with data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(["id", "arc_index", "seifert_circle_count", "bridge_number"])
        writer.writerow(["k1", "10", "5", "3"])
        writer.writerow(["k2", "12", "6", "4"])
        temp_path = Path(f.name)
    
    try:
        records = load_knot_data(temp_path)
        assert len(records) == 2
        assert records[0]["id"] == "k1"
        assert records[1]["bridge_number"] == "4"
    finally:
        temp_path.unlink()


def test_analyze_completeness_all_populated():
    """Test analysis when all invariants are populated."""
    records = [
        {"arc_index": "10", "seifert_circle_count": "5", "bridge_number": "3"},
        {"arc_index": "12", "seifert_circle_count": "6", "bridge_number": "4"},
    ]
    report = analyze_completeness(records)
    
    assert report.total_records == 2
    assert report.overall_completeness == 1.0
    assert report.passed is True
    assert len(report.stats) == 3
    for stat in report.stats:
        assert stat.completeness_ratio == 1.0


def test_analyze_completeness_partial_missing():
    """Test analysis with some missing values."""
    records = [
        {"arc_index": "10", "seifert_circle_count": "5", "bridge_number": "3"},
        {"arc_index": "", "seifert_circle_count": "6", "bridge_number": "4"},
        {"arc_index": "12", "seifert_circle_count": "", "bridge_number": ""},
    ]
    report = analyze_completeness(records)
    
    # Total records: 3, Total fields: 9
    # Populated: 8 (1 missing arc, 1 missing seifert, 1 missing bridge)
    # Wait, row 2: arc missing (1), row 3: seifert missing (1), bridge missing (1) -> 3 missing total
    # Total possible: 9. Populated: 6. Ratio: 6/9 = 0.666...
    
    assert report.total_records == 3
    # Check specific stats
    arc_stat = next(s for s in report.stats if s.invariant_name == "arc_index")
    assert arc_stat.missing_count == 1
    assert arc_stat.completeness_ratio == 2/3


def test_write_report_creates_file():
    """Test that write_report creates the markdown file."""
    report = CompletenessReport(
        total_records=10,
        overall_completeness=0.95,
        stats=[
            CompletenessStats("arc_index", 10, 10, 0, 1.0),
            CompletenessStats("seifert", 10, 9, 1, 0.9),
            CompletenessStats("bridge", 10, 10, 0, 1.0),
        ],
        passed=True
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_report.md"
        write_report(report, output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "Additional Invariant Completeness Report" in content
        assert "PASSED" in content
        assert "95.00%" in content
