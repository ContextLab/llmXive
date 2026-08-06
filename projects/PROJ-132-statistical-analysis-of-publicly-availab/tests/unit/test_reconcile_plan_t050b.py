"""
Tests for Task T050b: Reconcile GP Requirement.
"""
import os
import tempfile
from pathlib import Path
import pytest
from specs.reconcile_plan_t050b import reconcile_plan

class TestReconcilePlanT050b:
    """Test suite for the reconcile_plan function."""

    def test_reconcile_plan_updates_text(self, tmp_path):
        """Test that the function correctly updates the plan.md content."""
        plan_file = tmp_path / "plan.md"
        original_text = "This is a test with mandatory a priori Gaussian Process (GP) requirement."
        plan_file.write_text(original_text)

        result = reconcile_plan(plan_file)

        assert result is True
        updated_content = plan_file.read_text()
        expected_text = "This is a test with conditional (applied if Moran's I > 0.15) Gaussian Process (GP) requirement."
        assert updated_content == expected_text

    def test_reconcile_plan_file_not_found(self, tmp_path):
        """Test that the function returns False when the file is not found."""
        non_existent_file = tmp_path / "non_existent.md"
        result = reconcile_plan(non_existent_file)
        assert result is False

    def test_reconcile_plan_text_not_found(self, tmp_path):
        """Test that the function returns False if the target text is not present."""
        plan_file = tmp_path / "plan.md"
        content_without_target = "This plan has no GP requirement mentioned."
        plan_file.write_text(content_without_target)

        result = reconcile_plan(plan_file)

        # The function returns False if the old text was not found and replaced
        assert result is False
        assert plan_file.read_text() == content_without_target

    def test_reconcile_plan_idempotent(self, tmp_path):
        """Test that running the function twice doesn't break the file if already updated."""
        plan_file = tmp_path / "plan.md"
        # First, simulate the updated state
        updated_text = "This is a test with conditional (applied if Moran's I > 0.15) Gaussian Process (GP) requirement."
        plan_file.write_text(updated_text)

        result = reconcile_plan(plan_file)

        # If the old text isn't found but the new one is, it should ideally handle it gracefully.
        # Based on the implementation, if old text isn't found, it returns False unless new text is present.
        # Let's adjust the test expectation based on the implementation logic:
        # If old text not found -> returns False (unless new text is there, then True).
        # In this case, new text IS there, so it should return True.
        assert result is True
        assert plan_file.read_text() == updated_text