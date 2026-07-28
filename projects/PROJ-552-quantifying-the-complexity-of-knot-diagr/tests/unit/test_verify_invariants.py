"""Unit tests for code/data/verify_invariants.py"""
import math
from dataclasses import asdict
from pathlib import Path

import pytest
import pandas as pd

from code.data.verify_invariants import verify_invariants, VerificationEntry, VerificationReport
from code.data.computed_invariants import ComputedInvariantResult


class MockComputedInvariants:
    """Mock the compute_all_invariants function for testing."""
    @staticmethod
    def compute_all_invariants(record: dict) -> ComputedInvariantResult:
        # Return deterministic mock values based on knot_id or fixed
        knot_id = record.get("knot_id", record.get("id", "unknown"))
        # Simulate a computation that matches reference for some, mismatches for others
        if "match" in knot_id:
            return ComputedInvariantResult(
                arc_index=5.0,
                seifert_circle_count=3.0,
                bridge_number=2.0,
            )
        elif "mismatch" in knot_id:
            return ComputedInvariantResult(
                arc_index=10.0, # Intentionally wrong
                seifert_circle_count=3.0,
                bridge_number=2.0,
            )
        else:
            return ComputedInvariantResult(
                arc_index=5.0,
                seifert_circle_count=3.0,
                bridge_number=2.0,
            )

# Patch the import
import code.data.verify_invariants as verify_module
original_compute = verify_module.compute_all_invariants

def setup_module():
    verify_module.compute_all_invariants = MockComputedInvariants.compute_all_invariants

def teardown_module():
    verify_module.compute_all_invariants = original_compute


def test_verify_invariants_match():
    """Test that matching values are recorded as 'match'."""
    df = pd.DataFrame([
        {"knot_id": "test_match_01", "arc_index_ref": 5.0, "seifert_circle_count_ref": 3.0, "bridge_number_ref": 2.0},
    ])
    # Inject the dataframe into a temp CSV
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        df.to_csv(f.name, index=False)
        temp_path = Path(f.name)

    try:
        report = verify_invariants(temp_path, None)
        # Should have 3 entries (arc, seifert, bridge)
        assert len(report.entries) == 3
        for entry in report.entries:
            assert entry.status == "match"
        assert report.verified_count == 3
        assert report.mismatch_count == 0
    finally:
        temp_path.unlink()


def test_verify_invariants_mismatch():
    """Test that mismatched values are recorded as 'mismatch'."""
    df = pd.DataFrame([
        {"knot_id": "test_mismatch_01", "arc_index_ref": 5.0, "seifert_circle_count_ref": 3.0, "bridge_number_ref": 2.0},
    ])
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        df.to_csv(f.name, index=False)
        temp_path = Path(f.name)

    try:
        report = verify_invariants(temp_path, None)
        # Arc index should be 10.0 (mock) vs 5.0 (ref) -> mismatch
        arc_entry = next(e for e in report.entries if e.invariant_name == "arc_index")
        assert arc_entry.status == "mismatch"
        assert arc_entry.discrepancy == 5.0
        assert report.mismatch_count == 1
    finally:
        temp_path.unlink()


def test_verify_invariants_missing_ref():
    """Test that missing reference values are recorded as 'missing_ref'."""
    df = pd.DataFrame([
        {"knot_id": "test_no_ref_01"}, # No *_ref columns
    ])
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        df.to_csv(f.name, index=False)
        temp_path = Path(f.name)

    try:
        report = verify_invariants(temp_path, None)
        for entry in report.entries:
            assert entry.status == "missing_ref"
        assert report.missing_ref_count == 3
    finally:
        temp_path.unlink()


def test_verification_report_markdown():
    """Test markdown generation."""
    entries = [
        VerificationEntry(
            knot_id="K1",
            invariant_name="arc_index",
            computed_value=5.0,
            reference_value=5.0,
            source="computed",
            discrepancy=None,
            status="match",
            details=""
        ),
        VerificationEntry(
            knot_id="K2",
            invariant_name="arc_index",
            computed_value=10.0,
            reference_value=5.0,
            source="computed",
            discrepancy=5.0,
            status="mismatch",
            details="Test"
        ),
    ]
    report = VerificationReport(
        total_records=2,
        verified_count=1,
        mismatch_count=1,
        missing_ref_count=0,
        entries=entries
    )
    md = report.to_markdown()
    assert "Discrepancies Found: 1" in md
    assert "K2" in md
    assert "Test" in md