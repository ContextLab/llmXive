"""
Unit tests for provenance archiver functionality.

Tests verify that:
1. Provenance entries are correctly extracted from summaries
2. Required columns (url, repository_identifier, fetch_timestamp) are present
3. CSV file is correctly formatted and writable
4. Validation catches missing fields
"""
import csv
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.provenance_archiver import (
    extract_provenance_from_summary,
    archive_provenance,
    validate_provenance_log,
    REQUIRED_COLUMNS,
    PROVENANCE_LOG_PATH
)

class TestExtractProvenanceFromSummary:
    """Tests for extract_provenance_from_summary function."""
    
    def test_extract_basic_fields(self):
        """Test extraction of basic provenance fields."""
        summary = {
            "url": "https://example.com/ab-test-123",
            "fetch_timestamp": "2024-01-15T10:30:00Z"
        }
        
        provenance = extract_provenance_from_summary(summary)
        
        assert provenance["url"] == "https://example.com/ab-test-123"
        assert provenance["repository_identifier"] == "example.com"
        assert provenance["fetch_timestamp"] == "2024-01-15T10:30:00Z"
    
    def test_extract_without_timestamp(self):
        """Test extraction when fetch_timestamp is missing."""
        summary = {
            "url": "https://test.org/experiment"
        }
        
        provenance = extract_provenance_from_summary(summary)
        
        assert provenance["url"] == "https://test.org/experiment"
        assert provenance["repository_identifier"] == "test.org"
        # Should have a timestamp (current time or stored)
        assert "fetch_timestamp" in provenance
        assert provenance["fetch_timestamp"] is not None
    
    def test_extract_with_complex_url(self):
        """Test extraction with complex URL containing path and query."""
        summary = {
            "url": "https://shop.example.com/blog/ab-testing-results?year=2024",
            "fetch_timestamp": "2024-06-01T12:00:00Z"
        }
        
        provenance = extract_provenance_from_summary(summary)
        
        assert provenance["url"] == "https://shop.example.com/blog/ab-testing-results?year=2024"
        assert provenance["repository_identifier"] == "shop.example.com"
        assert provenance["fetch_timestamp"] == "2024-06-01T12:00:00Z"
    
    def test_extract_missing_url_raises(self):
        """Test that missing URL raises ValueError."""
        summary = {
            "fetch_timestamp": "2024-01-15T10:30:00Z"
        }
        
        with pytest.raises(ValueError, match="missing required.*url"):
            extract_provenance_from_summary(summary)
    
    def test_extract_all_required_fields_present(self):
        """Test that all required columns are present in output."""
        summary = {
            "url": "https://domain.io/test",
            "fetch_timestamp": "2024-01-01T00:00:00Z"
        }
        
        provenance = extract_provenance_from_summary(summary)
        
        for col in REQUIRED_COLUMNS:
            assert col in provenance, f"Missing required column: {col}"
            assert provenance[col], f"Column {col} is empty"

class TestArchiveProvenance:
    """Tests for archive_provenance function."""
    
    @pytest.fixture
    def temp_summaries_file(self, tmp_path):
        """Create a temporary summaries JSON file."""
        summaries = {
            "summaries": [
                {
                    "url": "https://example.com/test1",
                    "fetch_timestamp": "2024-01-15T10:00:00Z"
                },
                {
                    "url": "https://test.org/experiment",
                    "fetch_timestamp": "2024-01-15T11:00:00Z"
                }
            ]
        }
        file_path = tmp_path / "summaries.json"
        with open(file_path, "w") as f:
            json.dump(summaries, f)
        return file_path
    
    def test_archive_creates_csv(self, temp_summaries_file, tmp_path):
        """Test that archive creates CSV file with correct structure."""
        output_path = tmp_path / "provenance.csv"
        
        result_path = archive_provenance(
            summaries_path=temp_summaries_file,
            output_path=output_path,
            force_overwrite=True
        )
        
        assert result_path.exists()
        assert result_path == output_path
        
        # Verify CSV structure
        with open(result_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 2
            for row in rows:
                for col in REQUIRED_COLUMNS:
                    assert col in row
                    assert row[col], f"Column {col} is empty in row"
    
    def test_archive_with_list_input(self, tmp_path):
        """Test archiving when input is a list (not dict with 'summaries' key)."""
        summaries = [
            {"url": "https://a.com/test", "fetch_timestamp": "2024-01-01T00:00:00Z"},
            {"url": "https://b.com/test", "fetch_timestamp": "2024-01-02T00:00:00Z"}
        ]
        input_path = tmp_path / "summaries.json"
        with open(input_path, "w") as f:
            json.dump(summaries, f)
        
        output_path = tmp_path / "provenance.csv"
        archive_provenance(input_path, output_path, force_overwrite=True)
        
        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
    
    def test_archive_empty_summaries_creates_header_only(self, tmp_path):
        """Test that empty summaries create CSV with headers only."""
        summaries = {"summaries": []}
        input_path = tmp_path / "summaries.json"
        with open(input_path, "w") as f:
            json.dump(summaries, f)
        
        output_path = tmp_path / "provenance.csv"
        archive_provenance(input_path, output_path, force_overwrite=True)
        
        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0
            # Headers should exist
            assert reader.fieldnames == REQUIRED_COLUMNS
    
    def test_archive_missing_input_raises(self, tmp_path):
        """Test that missing input file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            archive_provenance(
                summaries_path=tmp_path / "nonexistent.json",
                output_path=tmp_path / "provenance.csv",
                force_overwrite=True
            )
    
    def test_archive_skips_on_existing_without_force(self, tmp_path):
        """Test that existing file is skipped without force_overwrite."""
        # Create input file
        summaries = {"summaries": [{"url": "https://test.com/x", "fetch_timestamp": "2024-01-01T00:00:00Z"}]}
        input_path = tmp_path / "summaries.json"
        with open(input_path, "w") as f:
            json.dump(summaries, f)
        
        # Create existing output
        output_path = tmp_path / "provenance.csv"
        output_path.write_text("existing,content\n1,2\n")
        
        result = archive_provenance(input_path, output_path, force_overwrite=False)
        
        # File should not be modified
        assert result.exists()
        assert output_path.read_text() == "existing,content\n1,2\n"

class TestValidateProvenanceLog:
    """Tests for validate_provenance_log function."""
    
    def test_validate_valid_log(self, tmp_path):
        """Test validation of a properly formatted provenance log."""
        output_path = tmp_path / "provenance.csv"
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            writer.writerow({
                "url": "https://example.com/test",
                "repository_identifier": "example.com",
                "fetch_timestamp": "2024-01-01T00:00:00Z"
            })
        
        is_valid, errors = validate_provenance_log(output_path)
        
        assert is_valid is True
        assert errors == []
    
    def test_validate_missing_file(self, tmp_path):
        """Test validation when file does not exist."""
        is_valid, errors = validate_provenance_log(tmp_path / "nonexistent.csv")
        
        assert is_valid is False
        assert len(errors) == 1
        assert "not found" in errors[0].lower()
    
    def test_validate_missing_columns(self, tmp_path):
        """Test validation when required columns are missing."""
        output_path = tmp_path / "provenance.csv"
        with open(output_path, "w") as f:
            f.write("url,other_column\n")
            f.write("https://test.com/x,value\n")
        
        is_valid, errors = validate_provenance_log(output_path)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("missing" in e.lower() for e in errors)
    
    def test_validate_empty_field_in_row(self, tmp_path):
        """Test validation when a row has empty required field."""
        output_path = tmp_path / "provenance.csv"
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            writer.writerow({
                "url": "https://example.com/test",
                "repository_identifier": "",  # Empty!
                "fetch_timestamp": "2024-01-01T00:00:00Z"
            })
        
        is_valid, errors = validate_provenance_log(output_path)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("missing" in e.lower() or "empty" in e.lower() for e in errors)

class TestProvenanceSchema:
    """Contract tests for provenance log schema compliance."""
    
    def test_all_required_columns_present(self):
        """Verify all required columns are defined."""
        assert "url" in REQUIRED_COLUMNS
        assert "repository_identifier" in REQUIRED_COLUMNS
        assert "fetch_timestamp" in REQUIRED_COLUMNS
        assert len(REQUIRED_COLUMNS) == 3
    
    def test_column_names_are_lowercase(self):
        """Verify column names follow naming convention."""
        for col in REQUIRED_COLUMNS:
            assert col == col.lower(), f"Column {col} should be lowercase"
            assert " " not in col, f"Column {col} should not contain spaces"
    
    def test_no_duplicate_columns(self):
        """Verify no duplicate column names."""
        assert len(REQUIRED_COLUMNS) == len(set(REQUIRED_COLUMNS))

class TestIntegration:
    """Integration tests for full provenance archiving workflow."""
    
    def test_full_workflow(self, tmp_path):
        """Test complete workflow from summaries to provenance log."""
        # Create input summaries
        summaries = {
            "summaries": [
                {
                    "url": "https://domain1.com/ab-test",
                    "fetch_timestamp": "2024-01-15T10:00:00Z",
                    "baseline_rate": 0.5,
                    "treatment_rate": 0.55
                },
                {
                    "url": "https://domain2.org/experiment",
                    "fetch_timestamp": "2024-01-16T11:00:00Z",
                    "baseline_rate": 0.3,
                    "treatment_rate": 0.33
                },
                {
                    "url": "https://domain3.io/test",
                    "fetch_timestamp": "2024-01-17T12:00:00Z",
                    "baseline_rate": 0.7,
                    "treatment_rate": 0.68
                }
            ]
        }
        input_path = tmp_path / "summaries.json"
        with open(input_path, "w") as f:
            json.dump(summaries, f)
        
        # Archive provenance
        output_path = tmp_path / "provenance.csv"
        archive_provenance(input_path, output_path, force_overwrite=True)
        
        # Validate output
        is_valid, errors = validate_provenance_log(output_path)
        assert is_valid is True, f"Validation failed: {errors}"
        
        # Verify content
        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 3
            
            # Check each row has correct structure
            expected_repos = ["domain1.com", "domain2.org", "domain3.io"]
            for i, row in enumerate(rows):
                assert row["url"] == summaries["summaries"][i]["url"]
                assert row["repository_identifier"] == expected_repos[i]
                assert row["fetch_timestamp"] == summaries["summaries"][i]["fetch_timestamp"]
