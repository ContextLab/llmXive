import json
import os
import tempfile
from pathlib import Path

import pytest

from code.research.verify_citations import verify_citations, load_json_file

def test_verify_citations_all_valid():
    """Test that verify_citations returns True and logs 'valid' when all scores >= 0.7."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_path = tmpdir_path / "validation_report.json"
        output_path = tmpdir_path / "verification_log.md"

        # Create valid mock data
        mock_data = [
            {"title": "Test 1", "doi": "10.1234/test1", "overlap_score": 0.8, "status": "valid"},
            {"title": "Test 2", "doi": "10.1234/test2", "overlap_score": 0.7, "status": "valid"}
        ]

        with open(input_path, 'w') as f:
            json.dump(mock_data, f)

        result = verify_citations(input_path, output_path)

        assert result is True
        assert output_path.exists()
        
        content = output_path.read_text()
        assert "Status: valid" in content
        assert "Test 1" in content
        assert "Test 2" in content

def test_verify_citations_some_invalid():
    """Test that verify_citations returns False and logs 'invalid' when any score < 0.7."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_path = tmpdir_path / "validation_report.json"
        output_path = tmpdir_path / "verification_log.md"

        # Create mock data with one invalid entry
        mock_data = [
            {"title": "Valid Title", "doi": "10.1234/valid", "overlap_score": 0.9, "status": "valid"},
            {"title": "Invalid Title", "doi": "10.1234/invalid", "overlap_score": 0.5, "status": "invalid"}
        ]

        with open(input_path, 'w') as f:
            json.dump(mock_data, f)

        result = verify_citations(input_path, output_path)

        assert result is False
        assert output_path.exists()

        content = output_path.read_text()
        assert "Status: invalid" in content
        assert "FAIL" in content
        assert "Invalid Title" in content
        assert "Valid Title" in content

def test_verify_citations_missing_file():
    """Test that verify_citations raises FileNotFoundError for missing input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "nonexistent.json"
        output_path = Path(tmpdir) / "log.md"

        with pytest.raises(FileNotFoundError):
            verify_citations(input_path, output_path)

def test_verify_citations_edge_case_07():
    """Test that exactly 0.7 is considered valid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_path = tmpdir_path / "validation_report.json"
        output_path = tmpdir_path / "verification_log.md"

        mock_data = [
            {"title": "Edge Case", "doi": "10.1234/edge", "overlap_score": 0.7, "status": "valid"}
        ]

        with open(input_path, 'w') as f:
            json.dump(mock_data, f)

        result = verify_citations(input_path, output_path)
        assert result is True
        assert "Status: valid" in output_path.read_text()

def test_verify_citations_edge_case_below_07():
    """Test that 0.69 is considered invalid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_path = tmpdir_path / "validation_report.json"
        output_path = tmpdir_path / "verification_log.md"

        mock_data = [
            {"title": "Below Threshold", "doi": "10.1234/below", "overlap_score": 0.69, "status": "invalid"}
        ]

        with open(input_path, 'w') as f:
            json.dump(mock_data, f)

        result = verify_citations(input_path, output_path)
        assert result is False
        assert "Status: invalid" in output_path.read_text()