import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from t003c_mock_data_guard import check_dev_mode, is_file_empty, run_guard_check, main

class TestT003cMockDataGuard:
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        # Setup: Create temporary directories for test isolation
        self.test_dir = tmp_path / "test_t003c"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create fixtures directory
        self.fixtures_dir = self.test_dir / "data" / "fixtures"
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)
        
        # Create processed directory
        self.processed_dir = self.test_dir / "data" / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Save original CWD
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        yield
        
        # Teardown: Restore CWD
        os.chdir(self.original_cwd)

    def test_check_dev_mode_true(self):
        """Test check_dev_mode returns True when DEV_MODE is set."""
        with patch.dict(os.environ, {"DEV_MODE": "true"}):
            assert check_dev_mode() is True
        with patch.dict(os.environ, {"DEV_MODE": "1"}):
            assert check_dev_mode() is True
        with patch.dict(os.environ, {"DEV_MODE": "yes"}):
            assert check_dev_mode() is True

    def test_check_dev_mode_false(self):
        """Test check_dev_mode returns False when DEV_MODE is not set or empty."""
        with patch.dict(os.environ, {}, clear=True):
            assert check_dev_mode() is False
        with patch.dict(os.environ, {"DEV_MODE": ""}):
            assert check_dev_mode() is False
        with patch.dict(os.environ, {"DEV_MODE": "false"}):
            assert check_dev_mode() is False

    def test_is_file_empty_missing(self):
        """Test is_file_empty returns True for missing file."""
        path = Path("non_existent_file.jsonl")
        assert is_file_empty(path) is True

    def test_is_file_empty_empty(self):
        """Test is_file_empty returns True for empty file."""
        path = self.fixtures_dir / "empty.jsonl"
        path.touch()
        assert is_file_empty(path) is True

    def test_is_file_empty_not_empty(self):
        """Test is_file_empty returns False for non-empty file."""
        path = self.fixtures_dir / "non_empty.jsonl"
        path.write_text('{"test": "data"}\n')
        assert is_file_empty(path) is False

    def test_run_guard_check_production_no_mock(self):
        """Test production mode with no mock data passes."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure mock file does not exist
            mock_path = self.fixtures_dir / "mock_trajectories.jsonl"
            if mock_path.exists():
                mock_path.unlink()
            
            result = run_guard_check()
            assert result["status"] == "passed"
            assert result["dev_mode"] is False

    def test_run_guard_check_production_mock_empty(self):
        """Test production mode with empty mock data passes."""
        with patch.dict(os.environ, {}, clear=True):
            mock_path = self.fixtures_dir / "mock_trajectories.jsonl"
            mock_path.touch() # Create empty file
            
            result = run_guard_check()
            assert result["status"] == "passed"
            assert result["dev_mode"] is False

    def test_run_guard_check_production_mock_exists(self):
        """Test production mode with non-empty mock data raises RuntimeError."""
        with patch.dict(os.environ, {}, clear=True):
            mock_path = self.fixtures_dir / "mock_trajectories.jsonl"
            mock_path.write_text('{"trajectory_id": "test_1", "turn": 1}\n')
            
            with pytest.raises(RuntimeError) as excinfo:
                run_guard_check()
            assert "Mock data detected in production run" in str(excinfo.value)

    def test_run_guard_check_dev_mode_mock_exists(self):
        """Test dev mode with non-empty mock data passes."""
        with patch.dict(os.environ, {"DEV_MODE": "true"}):
            mock_path = self.fixtures_dir / "mock_trajectories.jsonl"
            mock_path.write_text('{"trajectory_id": "test_1", "turn": 1}\n')
            
            result = run_guard_check()
            assert result["status"] == "passed"
            assert result["dev_mode"] is True
            assert result["mock_data_exists"] is True

    def test_run_guard_check_writes_output(self):
        """Test that run_guard_check writes the JSON output file."""
        with patch.dict(os.environ, {}, clear=True):
            result = run_guard_check()
            output_path = Path("data/processed/dev_mode_guard.json")
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert "status" in loaded
            assert "timestamp" in loaded
            assert loaded["status"] == "passed"