"""
Tests for code/verify_plan_status.py
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

# Import the module functions
from verify_plan_status import (
    check_plan_content,
    get_current_status,
    update_status,
    PLAN_FILE_NAME
)


class TestCheckPlanContent:
    def test_plan_not_found(self, tmp_path):
        """Test behavior when plan.md does not exist."""
        non_existent_path = tmp_path / "non_existent.md"
        has_bhm, message = check_plan_content(non_existent_path)
        assert has_bhm is False
        assert "not found" in message

    def test_plan_without_bhm(self, tmp_path):
        """Test plan without BHM reference."""
        plan_file = tmp_path / PLAN_FILE_NAME
        plan_file.write_text("# My Plan\n\nNo BHM here.")
        has_bhm, message = check_plan_content(plan_file)
        assert has_bhm is False
        assert "does not reference" in message

    def test_plan_with_bhm_keyword(self, tmp_path):
        """Test plan with BHM keyword."""
        plan_file = tmp_path / PLAN_FILE_NAME
        plan_file.write_text("# Plan\n\nWe will use BHM methodology.")
        has_bhm, message = check_plan_content(plan_file)
        assert has_bhm is True
        assert "references" in message

    def test_plan_with_bhm_full_name(self, tmp_path):
        """Test plan with full BHM name."""
        plan_file = tmp_path / PLAN_FILE_NAME
        plan_file.write_text("# Plan\n\nBayesian Hierarchical Model is required.")
        has_bhm, message = check_plan_content(plan_file)
        assert has_bhm is True
        assert "references" in message

    def test_plan_with_bhm_mixed_case(self, tmp_path):
        """Test plan with mixed case BHM."""
        plan_file = tmp_path / PLAN_FILE_NAME
        plan_file.write_text("# Plan\n\nWe use BhM and bhm.")
        has_bhm, message = check_plan_content(plan_file)
        assert has_bhm is True

class TestGetCurrentStatus:
    def test_no_status(self, tmp_path):
        """Test plan without status field."""
        plan_file = tmp_path / PLAN_FILE_NAME
        plan_file.write_text("# Plan\n\nContent only.")
        status = get_current_status(plan_file)
        assert status == "UNKNOWN"

    def test_status_pending(self, tmp_path):
        """Test plan with PENDING status."""
        plan_file = tmp_path / PLAN_FILE_NAME
        plan_file.write_text("# Plan\n\nStatus: PENDING\n\nContent.")
        status = get_current_status(plan_file)
        assert status == "PENDING"

    def test_status_ratified(self, tmp_path):
        """Test plan with RATIFIED status."""
        plan_file = tmp_path / PLAN_FILE_NAME
        plan_file.write_text("## Status: RATIFIED\n\nContent.")
        status = get_current_status(plan_file)
        assert status == "RATIFIED"

    def test_status_lowercase(self, tmp_path):
        """Test plan with lowercase status."""
        plan_file = tmp_path / PLAN_FILE_NAME
        plan_file.write_text("status: pending\n\nContent.")
        status = get_current_status(plan_file)
        assert status == "PENDING"

    def test_project_status(self, tmp_path):
        """Test plan with Project Status field."""
        plan_file = tmp_path / PLAN_FILE_NAME
        plan_file.write_text("## Project Status: PENDING\n\nContent.")
        status = get_current_status(plan_file)
        assert status == "PENDING"

class TestUpdateStatus:
    def test_update_pending_to_ratified(self, tmp_path):
        """Test updating PENDING to RATIFIED."""
        plan_file = tmp_path / PLAN_FILE_NAME
        plan_file.write_text("# Plan\n\nStatus: PENDING\n\nContent.")
        success = update_status(plan_file, "RATIFIED")
        assert success is True
        content = plan_file.read_text()
        assert "Status: RATIFIED" in content
        assert "Status: PENDING" not in content

    def test_append_status_if_missing(self, tmp_path):
        """Test appending status when missing."""
        plan_file = tmp_path / PLAN_FILE_NAME
        plan_file.write_text("# Plan\n\nContent only.")
        success = update_status(plan_file, "RATIFIED")
        assert success is True
        content = plan_file.read_text()
        assert "Status: RATIFIED" in content

    def test_update_project_status(self, tmp_path):
        """Test updating Project Status field."""
        plan_file = tmp_path / PLAN_FILE_NAME
        plan_file.write_text("## Project Status: PENDING\n\nContent.")
        success = update_status(plan_file, "RATIFIED")
        assert success is True
        content = plan_file.read_text()
        assert "Project Status: RATIFIED" in content

    def test_file_not_found(self, tmp_path):
        """Test update when file does not exist."""
        non_existent = tmp_path / "no_file.md"
        success = update_status(non_existent, "RATIFIED")
        assert success is False