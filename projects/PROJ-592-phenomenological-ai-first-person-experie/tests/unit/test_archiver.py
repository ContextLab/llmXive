"""
Unit tests for the archiver module.

Tests FR-007: Packaging prompts, seeds, scripts, and anonymized ratings
for public reproducibility.
"""
import os
import json
import csv
import tempfile
import shutil
from pathlib import Path
import pytest

from utils.archiver import (
    ArchiverError,
    anonymize_rating_data,
    anonymize_json_data,
    create_archive_manifest,
    prepare_anonymized_ratings,
    create_reproducibility_archive,
    run_archiver,
    ANONYMIZE_FIELDS,
)
from utils.io import safe_write_csv, safe_write_json, load_json, load_csv


class TestAnonymizeRatingData:
    """Tests for CSV data anonymization."""

    def test_anonymize_single_record(self, tmp_path):
        """Test anonymization of a single record with identifiers."""
        input_file = tmp_path / "ratings.csv"
        output_file = tmp_path / "anonymized_ratings.csv"
        
        # Create test data
        rows = [
            {"rater_id": "rater_001", "score": 5, "comment": "Good"},
        ]
        safe_write_csv(input_file, rows)
        
        # Anonymize
        count = anonymize_rating_data(input_file, output_file)
        
        assert count == 1
        assert output_file.exists()
        
        # Verify anonymization
        result = load_csv(output_file)
        assert len(result) == 1
        assert result[0]["rater_id"].startswith("anon_")
        assert result[0]["rater_id"] != "rater_001"
        assert result[0]["score"] == 5

    def test_anonymize_multiple_records(self, tmp_path):
        """Test anonymization preserves consistency across records."""
        input_file = tmp_path / "ratings.csv"
        output_file = tmp_path / "anonymized_ratings.csv"
        
        rows = [
            {"rater_id": "rater_001", "score": 5},
            {"rater_id": "rater_002", "score": 4},
            {"rater_id": "rater_001", "score": 3},  # Same rater
        ]
        safe_write_csv(input_file, rows)
        
        count = anonymize_rating_data(input_file, output_file)
        
        assert count == 3
        result = load_csv(output_file)
        
        # First and third records should have same anonymized ID
        assert result[0]["rater_id"] == result[2]["rater_id"]
        assert result[0]["rater_id"] != result[1]["rater_id"]

    def test_anonymize_missing_file(self, tmp_path):
        """Test handling of missing input file."""
        input_file = tmp_path / "nonexistent.csv"
        output_file = tmp_path / "output.csv"
        
        count = anonymize_rating_data(input_file, output_file)
        assert count == 0
        assert not output_file.exists()

    def test_anonymize_preserves_non_id_fields(self, tmp_path):
        """Test that non-identifier fields are preserved."""
        input_file = tmp_path / "ratings.csv"
        output_file = tmp_path / "output.csv"
        
        rows = [
            {
                "rater_id": "rater_001",
                "score": 5,
                "timestamp": "2024-01-01",
                "condition": "direct",
                "comment": "Excellent report"
            },
        ]
        safe_write_csv(input_file, rows)
        
        anonymize_rating_data(input_file, output_file)
        result = load_csv(output_file)
        
        assert result[0]["score"] == 5
        assert result[0]["timestamp"] == "2024-01-01"
        assert result[0]["condition"] == "direct"
        assert result[0]["comment"] == "Excellent report"


class TestAnonymizeJsonData:
    """Tests for JSON data anonymization."""

    def test_anonymize_simple_json(self, tmp_path):
        """Test anonymization of simple JSON structure."""
        input_file = tmp_path / "ratings.json"
        output_file = tmp_path / "anonymized.json"
        
        data = [
            {"rater_id": "user_123", "score": 4},
            {"rater_id": "user_456", "score": 5},
        ]
        safe_write_json(input_file, data)
        
        count = anonymize_json_data(input_file, output_file)
        
        assert count == 2
        result = load_json(output_file)
        
        assert result[0]["rater_id"].startswith("anon_")
        assert result[1]["rater_id"].startswith("anon_")
        assert result[0]["rater_id"] != result[1]["rater_id"]

    def test_anonymize_nested_json(self, tmp_path):
        """Test anonymization in nested structures."""
        input_file = tmp_path / "nested.json"
        output_file = tmp_path / "output.json"
        
        data = [
            {
                "session": {
                    "user_id": "sess_001",
                    "data": {"score": 5}
                },
                "participant_id": "p_001"
            },
        ]
        safe_write_json(input_file, data)
        
        count = anonymize_json_data(input_file, output_file)
        
        assert count == 2
        result = load_json(output_file)
        
        assert result[0]["session"]["user_id"].startswith("anon_")
        assert result[0]["participant_id"].startswith("anon_")

    def test_anonymize_missing_file(self, tmp_path):
        """Test handling of missing JSON file."""
        input_file = tmp_path / "nonexistent.json"
        output_file = tmp_path / "output.json"
        
        count = anonymize_json_data(input_file, output_file)
        assert count == 0


class TestCreateArchiveManifest:
    """Tests for manifest creation."""

    def test_manifest_creates_correct_structure(self, tmp_path):
        """Test that manifest contains required fields."""
        project_root = tmp_path / "project"
        output_dir = tmp_path / "output"
        project_root.mkdir()
        output_dir.mkdir()
        
        # Create some dummy files
        (project_root / "code").mkdir()
        (project_root / "data").mkdir()
        (project_root / "README.md").write_text("test")
        
        manifest = create_archive_manifest(project_root, output_dir, "test.tar.gz")
        
        assert "archive_name" in manifest
        assert "created_at" in manifest
        assert "project_root" in manifest
        assert "directories_included" in manifest
        assert "files_included" in manifest
        assert manifest["archive_name"] == "test.tar.gz"
        assert manifest["anonymization_applied"] is True

    def test_manifest_records_existing_files(self, tmp_path):
        """Test that manifest records files that exist."""
        project_root = tmp_path / "project"
        output_dir = tmp_path / "output"
        project_root.mkdir()
        output_dir.mkdir()
        
        # Create files that match ARCHIVE_FILES
        (project_root / "code").mkdir()
        (project_root / "code" / "config.py").write_text("test")
        (project_root / "README.md").write_text("test")
        
        manifest = create_archive_manifest(project_root, output_dir, "test.tar.gz")
        
        assert "code/config.py" in manifest["files_included"]
        assert "README.md" in manifest["files_included"]


class TestCreateReproducibilityArchive:
    """Integration tests for full archive creation."""

    def test_archive_creation(self, tmp_path):
        """Test full archive creation process."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        # Create minimal project structure
        dirs = [
            "code/generation",
            "code/analysis",
            "data/prompts",
            "data/raw",
            "specs/contracts",
        ]
        for d in dirs:
            (project_root / d).mkdir(parents=True)
            
        # Create a dummy file
        (project_root / "code" / "test.py").write_text("print('hello')")
        (project_root / "data" / "prompts" / "test.json").write_text("[]")
        
        output_dir = project_root / "data" / "archives"
        archive_name = "test_archive.tar.gz"
        
        archive_path = create_reproducibility_archive(
            project_root, output_dir, archive_name
        )
        
        assert Path(archive_path).exists()
        assert archive_path == str(output_dir / archive_name)

    def test_archive_contains_manifest(self, tmp_path):
        """Test that archive contains a manifest file."""
        import tarfile
        
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        # Create minimal structure
        (project_root / "code").mkdir()
        (project_root / "data").mkdir()
        
        output_dir = project_root / "data" / "archives"
        archive_path = create_reproducibility_archive(project_root, output_dir)
        
        # Extract and check manifest
        with tarfile.open(archive_path, "r:gz") as tar:
            names = tar.getnames()
            assert any("ARCHIVE_MANIFEST.json" in n for n in names)


class TestRunArchiver:
    """Tests for the run_archiver function."""

    def test_run_archiver_success(self, tmp_path):
        """Test successful execution of run_archiver."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        # Create minimal structure
        (project_root / "code").mkdir()
        (project_root / "data").mkdir()
        
        output_dir = project_root / "data" / "archives"
        
        result = run_archiver(project_root, output_dir)
        
        assert result["status"] == "success"
        assert "archive_path" in result
        assert Path(result["archive_path"]).exists()

    def test_run_archiver_default_paths(self, tmp_path):
        """Test run_archiver with default paths."""
        # Change to temp directory to avoid affecting real project
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Create minimal structure
            (tmp_path / "code").mkdir()
            (tmp_path / "data").mkdir()
            
            result = run_archiver()
            
            assert result["status"] == "success"
            # Default output should be in data/archives/
            assert "data/archives" in result["archive_path"]
        finally:
            os.chdir(old_cwd)


class TestAnonymizeFields:
    """Tests for ANONYMIZE_FIELDS configuration."""

    def test_all_expected_fields_present(self):
        """Test that expected anonymization fields are configured."""
        expected_fields = [
            "rater_id",
            "participant_id",
            "user_id",
        ]
        
        for field in expected_fields:
            assert field in ANONYMIZE_FIELDS