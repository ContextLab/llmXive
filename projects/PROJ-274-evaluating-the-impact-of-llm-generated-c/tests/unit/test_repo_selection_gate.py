import json
import os
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta

import pytest

# Import the functions to test
import sys
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.run_repo_selection_gate import verify_data_freshness, verify_tolerances

class TestVerifyDataFreshness:
    def test_file_not_found(self, tmp_path):
        """Test that missing file returns False."""
        result = verify_data_freshness(str(tmp_path / "nonexistent.json"))
        assert result is False

    def test_file_stale(self, tmp_path):
        """Test that stale file returns False."""
        file_path = tmp_path / "stale.json"
        file_path.write_text('{"data": "test"}')
        
        # Manipulate modification time to be 2 hours ago
        now = time.time()
        os.utime(file_path, (now - 7200, now - 7200))
        
        result = verify_data_freshness(str(file_path), max_age_hours=1)
        assert result is False

    def test_file_fresh(self, tmp_path):
        """Test that fresh file returns True."""
        file_path = tmp_path / "fresh.json"
        file_path.write_text('{"data": "test"}')
        
        result = verify_data_freshness(str(file_path), max_age_hours=1)
        assert result is True

    def test_run_id_mismatch(self, tmp_path):
        """Test that mismatched run_id returns False."""
        file_path = tmp_path / "run_id.json"
        data = {"metadata": {"run_id": "old_run"}}
        file_path.write_text(json.dumps(data))
        
        result = verify_data_freshness(str(file_path), run_id="new_run")
        assert result is False

    def test_run_id_match(self, tmp_path):
        """Test that matching run_id returns True."""
        file_path = tmp_path / "run_id.json"
        data = {"metadata": {"run_id": "current_run"}}
        file_path.write_text(json.dumps(data))
        
        result = verify_data_freshness(str(file_path), run_id="current_run")
        assert result is True

class TestVerifyTolerances:
    def test_tolerance_fail_loc(self):
        """Test that failing LOC tolerance returns False."""
        data = {
            "selected_repos": [{"url": "http://test.com"}],
            "tolerance_check": {"loc": False, "cc": True}
        }
        assert verify_tolerances(data) is False

    def test_tolerance_fail_cc(self):
        """Test that failing CC tolerance returns False."""
        data = {
            "selected_repos": [{"url": "http://test.com"}],
            "tolerance_check": {"loc": True, "cc": False}
        }
        assert verify_tolerances(data) is False

    def test_no_selected_repos(self):
        """Test that empty selected_repos returns False."""
        data = {
            "selected_repos": [],
            "tolerance_check": {"loc": True, "cc": True}
        }
        assert verify_tolerances(data) is False

    def test_success(self):
        """Test that passing all checks returns True."""
        data = {
            "selected_repos": [{"url": "http://test.com"}],
            "tolerance_check": {"loc": True, "cc": True}
        }
        assert verify_tolerances(data) is True
