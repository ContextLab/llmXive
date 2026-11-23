"""Unit tests for code/data/verify_invariants.py."""
import pytest
from pathlib import Path
import pandas as pd
from dataclasses import dataclass

# Mock the computed_invariants module for testing
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_knot_data():
    """Create mock knot data for testing."""
    data = {
        "knot_id": ["3_1", "4_1", "5_1"],
        "crossing_number": [3, 4, 5],
        "braid_index": [2, 2, 2],
        "hyperbolic_volume": [1.0, 2.0, 3.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_computed_result():
    """Create a mock ComputedInvariantResult."""
    from data.computed_invariants import ComputedInvariantResult
    return ComputedInvariantResult(
        arc_index=3,
        seifert_circle_count=2,
        bridge_number=2,
        # Add other fields as needed
    )

def test_load_filtered_knots(mock_knot_data, tmp_path):
    """Test loading filtered knots from CSV."""
    from code.data.verify_invariants import load_filtered_knots

    csv_path = tmp_path / "test.csv"
    mock_knot_data.to_csv(csv_path, index=False)

    df = load_filtered_knots(csv_path)
    assert len(df) == 3
    assert "knot_id" in df.columns

def test_verify_invariants_logic(mock_knot_data, mock_computed_result):
    """Test invariant verification logic."""
    from code.data.verify_invariants import verify_invariants

    with patch("code.data.verify_invariants.compute_all_invariants", return_value=mock_computed_result):
        report = verify_invariants(mock_knot_data)

    assert report.total_records == 3
    assert report.computed_count > 0
    # Check that arc_index >= crossing_number logic is applied
    for entry in report.entries:
        if entry.invariant_name == "arc_index":
            assert entry.computed_value >= 3  # Min crossing number in mock data

def test_write_report(tmp_path):
    """Test report generation."""
    from code.data.verify_invariants import write_report, VerificationReport, VerificationEntry

    report = VerificationReport(
        timestamp="2026-01-01T00:00:00",
        total_records=1,
        computed_count=1,
        reference_count=0,
        match_count=1,
        discrepancy_count=0,
        entries=[
            VerificationEntry(
                knot_id="3_1",
                invariant_name="arc_index",
                computed_value=3,
                reference_value=None,
                match=True
            )
        ]
    )

    output_path = tmp_path / "report.md"
    write_report(report, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    assert "Computed Invariant Verification Report" in content
    assert "3_1" in content
    assert "arc_index" in content
