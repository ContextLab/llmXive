"""
Unit tests for Task T050c: Update Runtime Budget.
"""
import os
import tempfile
from pathlib import Path
import pytest
from specs.reconcile_plan_t050c import reconcile_plan


class TestReconcilePlanT050c:
    """Test suite for the reconcile_plan function in T050c."""

    def test_update_runtime_constraint(self, tmp_path):
        """Test that the runtime constraint is updated from 5.5-hour to 6-hour."""
        plan_content = """
        # Project Plan

        ## Runtime Constraints
        The pipeline is estimated to run in 5.5-hour.

        SC-005: Runtime must be under 5.5-hour.
        """
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(plan_content)

        result = reconcile_plan(plan_file)

        assert result is True
        updated_content = plan_file.read_text()
        assert "6-hour" in updated_content
        assert "5.5-hour" not in updated_content

    def test_already_updated(self, tmp_path):
        """Test that no changes are made if the constraint is already 6-hour."""
        plan_content = """
        # Project Plan

        ## Runtime Constraints
        The pipeline is estimated to run in 6-hour.
        """
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(plan_content)

        result = reconcile_plan(plan_file)

        assert result is True
        updated_content = plan_file.read_text()
        assert "6-hour" in updated_content
        # Ensure we didn't accidentally change it to something else
        assert updated_content.count("6-hour") == 1

    def test_missing_old_constraint_add_new(self, tmp_path):
        """Test adding the 6-hour constraint when the old one is missing."""
        plan_content = """
        # Project Plan

        ## Other Sections
        Some other content.
        """
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(plan_content)

        result = reconcile_plan(plan_file)

        assert result is True
        updated_content = plan_file.read_text()
        assert "6-hour" in updated_content

    def test_missing_file(self, tmp_path):
        """Test handling of a missing plan file."""
        plan_file = tmp_path / "nonexistent.md"

        result = reconcile_plan(plan_file)

        assert result is False

    def test_sc005_reference_update(self, tmp_path):
        """Test updating SC-005 reference specifically."""
        plan_content = """
        # Project Plan

        SC-005: Runtime must be under 5.5-hour.
        """
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(plan_content)

        result = reconcile_plan(plan_file)

        assert result is True
        updated_content = plan_file.read_text()
        assert "6-hour" in updated_content
        assert "5.5-hour" not in updated_content