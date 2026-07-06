"""
Unit tests for extraction verification logic.

These tests assert that the CSV columns exist and the row count
meets the minimum viable dataset requirement (FR-001).
"""
import csv
import tempfile
import os
from pathlib import Path
import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from extraction.verify_extraction import verify_csv_structure, REQUIRED_COLUMNS, MIN_ROWS

def create_test_csv(rows: int, include_required: bool = True) -> Path:
    """Helper to create a temporary CSV file for testing."""
    fd, path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        
        for i in range(rows):
            row = {
                'snippet_id': f'snippet_{i}',
                'repo_url': 'https://github.com/test/repo.git',
                'file_path': f'path/to/file_{i}.py',
                'median_commit_age': 30.5,
                'snippet_content': 'def test(): pass',
                'token_count': 50,
                'complexity': 1,
                'token_length': 50
            }
            if not include_required:
                row['snippet_content'] = None
            writer.writerow(row)
    
    return Path(path)

class TestExtractionVerification:
    
    def test_csv_with_correct_columns_passes(self):
        """Test that a CSV with all required columns passes verification."""
        csv_path = create_test_csv(rows=800)
        try:
            result = verify_csv_structure(csv_path)
            assert result is True
        finally:
            os.unlink(csv_path)
    
    def test_csv_missing_columns_fails(self):
        """Test that a CSV missing required columns fails verification."""
        fd, path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['snippet_id', 'repo_url'])
            writer.writeheader()
            writer.writerow({'snippet_id': '1', 'repo_url': 'test'})
        
        try:
            result = verify_csv_structure(Path(path))
            assert result is False
        finally:
            os.unlink(path)
    
    def test_csv_with_insufficient_rows_fails(self):
        """Test that a CSV with fewer than MIN_ROWS fails verification."""
        csv_path = create_test_csv(rows=100)
        try:
            result = verify_csv_structure(csv_path)
            assert result is False
        finally:
            os.unlink(csv_path)
    
    def test_csv_with_null_content_fails(self):
        """Test that rows with null snippet_content are not counted as valid."""
        csv_path = create_test_csv(rows=1000, include_required=False)
        try:
            result = verify_csv_structure(csv_path)
            # Should fail because all rows have null content
            assert result is False
        finally:
            os.unlink(csv_path)
    
    def test_nonexistent_file_fails(self):
        """Test that a nonexistent file fails verification."""
        result = verify_csv_structure(Path("/nonexistent/path.csv"))
        assert result is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])