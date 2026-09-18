"""
Unit tests for T017b Checkpoint Validation logic.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from checkpoint_validator import validate_checkpoint

class TestCheckpointValidation:
    def create_temp_file(self, content, filename="baseline_scores.json"):
        """Helper to create a temporary file with given content."""
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f)
        return file_path

    def test_missing_file(self, monkeypatch):
        """Test behavior when the file does not exist."""
        # Monkeypatch the path to a non-existent file
        import checkpoint_validator as cv
        original_path = cv.BASELINE_FILE
        cv.BASELINE_FILE = Path("/nonexistent/path/file.json")
        
        try:
            result = validate_checkpoint()
            assert result is False
        finally:
            cv.BASELINE_FILE = original_path

    def test_invalid_json(self, monkeypatch):
        """Test behavior when JSON is invalid."""
        content = "{ invalid json }"
        file_path = self.create_temp_file(content)
        
        import checkpoint_validator as cv
        original_path = cv.BASELINE_FILE
        cv.BASELINE_FILE = file_path
        
        try:
            result = validate_checkpoint()
            assert result is False
        finally:
            cv.BASELINE_FILE = original_path
            file_path.parent.rmdir()

    def test_missing_top_level_keys(self, monkeypatch):
        """Test behavior when top-level keys are missing."""
        content = {"scores": []}
        file_path = self.create_temp_file(content)
        
        import checkpoint_validator as cv
        original_path = cv.BASELINE_FILE
        cv.BASELINE_FILE = file_path
        
        try:
            result = validate_checkpoint()
            assert result is False
        finally:
            cv.BASELINE_FILE = original_path
            file_path.parent.rmdir()

    def test_wrong_total_entries(self, monkeypatch):
        """Test behavior when total_entries is not 100."""
        content = {"scores": [], "total_entries": 50}
        file_path = self.create_temp_file(content)
        
        import checkpoint_validator as cv
        original_path = cv.BASELINE_FILE
        cv.BASELINE_FILE = file_path
        
        try:
            result = validate_checkpoint()
            assert result is False
        finally:
            cv.BASELINE_FILE = original_path
            file_path.parent.rmdir()

    def test_wrong_scores_count(self, monkeypatch):
        """Test behavior when scores list length is not 100."""
        content = {"scores": [{"seed": 1, "score": 0.5, "timestamp": "2023-01-01"}] * 99, "total_entries": 100}
        file_path = self.create_temp_file(content)
        
        import checkpoint_validator as cv
        original_path = cv.BASELINE_FILE
        cv.BASELINE_FILE = file_path
        
        try:
            result = validate_checkpoint()
            assert result is False
        finally:
            cv.BASELINE_FILE = original_path
            file_path.parent.rmdir()

    def test_missing_entry_keys(self, monkeypatch):
        """Test behavior when an entry is missing required keys."""
        content = {
            "scores": [{"seed": 1, "score": 0.5, "timestamp": "2023-01-01"}] * 99 + [{"seed": 2}],
            "total_entries": 100
        }
        file_path = self.create_temp_file(content)
        
        import checkpoint_validator as cv
        original_path = cv.BASELINE_FILE
        cv.BASELINE_FILE = file_path
        
        try:
            result = validate_checkpoint()
            assert result is False
        finally:
            cv.BASELINE_FILE = original_path
            file_path.parent.rmdir()

    def test_invalid_types_in_entry(self, monkeypatch):
        """Test behavior when entry values have wrong types."""
        content = {
            "scores": [{"seed": "not_int", "score": 0.5, "timestamp": "2023-01-01"}] * 100,
            "total_entries": 100
        }
        file_path = self.create_temp_file(content)
        
        import checkpoint_validator as cv
        original_path = cv.BASELINE_FILE
        cv.BASELINE_FILE = file_path
        
        try:
            result = validate_checkpoint()
            assert result is False
        finally:
            cv.BASELINE_FILE = original_path
            file_path.parent.rmdir()

    def test_valid_file(self, monkeypatch):
        """Test behavior when file is valid."""
        content = {
            "scores": [{"seed": i, "score": float(i)/100, "timestamp": "2023-01-01T00:00:00Z"} for i in range(100)],
            "total_entries": 100
        }
        file_path = self.create_temp_file(content)
        
        import checkpoint_validator as cv
        original_path = cv.BASELINE_FILE
        cv.BASELINE_FILE = file_path
        
        try:
            result = validate_checkpoint()
            assert result is True
        finally:
            cv.BASELINE_FILE = original_path
            file_path.parent.rmdir()