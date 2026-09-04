"""
Unit tests for code/update_readme.py (T012c).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the functions to test
from code.update_readme import (
    load_exclusion_log,
    parse_verified_datasets,
    generate_dataset_status_section,
    update_readme,
    run_t013,
    get_data_dir,
    get_processed_dir
)


class TestLoadExclusionLog:
    def test_load_existing_log(self, tmp_path):
        """Test loading an existing exclusion log."""
        exclusion_log_path = tmp_path / "exclusion_log.json"
        test_data = [
            {"dataset_id": "123", "reason": "Missing columns"},
            {"dataset_id": "456", "reason": "Invalid format"}
        ]
        exclusion_log_path.write_text(json.dumps(test_data))

        result = load_exclusion_log(exclusion_log_path)
        assert result == test_data

    def test_load_nonexistent_log(self, tmp_path):
        """Test loading a non-existent exclusion log returns empty list."""
        exclusion_log_path = tmp_path / "nonexistent.json"

        result = load_exclusion_log(exclusion_log_path)
        assert result == []

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON returns empty list."""
        exclusion_log_path = tmp_path / "invalid.json"
        exclusion_log_path.write_text("not valid json")

        result = load_exclusion_log(exclusion_log_path)
        assert result == []

    def test_load_non_list_json(self, tmp_path):
        """Test loading JSON that is not a list returns empty list."""
        exclusion_log_path = tmp_path / "non_list.json"
        exclusion_log_path.write_text(json.dumps({"key": "value"}))

        result = load_exclusion_log(exclusion_log_path)
        assert result == []


class TestParseVerifiedDatasets:
    def test_parse_valid_readme(self, tmp_path):
        """Test parsing a valid README with verified datasets."""
        readme_path = tmp_path / "README.md"
        readme_content = """
        # Data Directory

        ## Verified datasets
        - id: 123
          source: openml
          type: time_perception
        - id: 456
          source: huggingface
          type: time_perception

        ## Other Section
        Content here.
        """
        readme_path.write_text(readme_content)

        result = parse_verified_datasets(readme_path)

        assert "123" in result
        assert result["123"]["source"] == "openml"
        assert result["123"]["type"] == "time_perception"
        assert "456" in result
        assert result["456"]["source"] == "huggingface"

    def test_parse_empty_readme(self, tmp_path):
        """Test parsing an empty README returns empty dict."""
        readme_path = tmp_path / "README.md"
        readme_path.write_text("# Data Directory")

        result = parse_verified_datasets(readme_path)
        assert result == {}

    def test_parse_readme_no_verified_section(self, tmp_path):
        """Test parsing README without verified datasets section."""
        readme_path = tmp_path / "README.md"
        readme_path.write_text("# Data Directory\n\nSome content.")

        result = parse_verified_datasets(readme_path)
        assert result == {}


class TestGenerateDatasetStatusSection:
    def test_generate_with_exclusions(self):
        """Test generating status section with excluded datasets."""
        verified_datasets = {
            "123": {"source": "openml", "type": "time_perception"},
            "456": {"source": "huggingface", "type": "time_perception"}
        }
        exclusion_log = [
            {"dataset_id": "123", "reason": "Missing columns"}
        ]

        result = generate_dataset_status_section(verified_datasets, exclusion_log)

        assert "### Dataset Status" in result
        assert "openml_123: excluded (reason: Missing columns)" in result
        assert "huggingface_456: valid" in result

    def test_generate_no_exclusions(self):
        """Test generating status section with no exclusions."""
        verified_datasets = {
            "123": {"source": "openml", "type": "time_perception"}
        }
        exclusion_log = []

        result = generate_dataset_status_section(verified_datasets, exclusion_log)

        assert "### Dataset Status" in result
        assert "openml_123: valid" in result
        assert "excluded" not in result


class TestUpdateReadme:
    def test_update_existing_readme(self, tmp_path):
        """Test updating an existing README with new status section."""
        readme_path = tmp_path / "README.md"
        readme_content = """
        # Data Directory

        ## Verified datasets
        - id: 123
          source: openml
          type: time_perception

        ## Exclusion Logs
        Old content.
        """
        readme_path.write_text(readme_content)

        exclusion_log = [
            {"dataset_id": "123", "reason": "Missing columns"}
        ]
        verified_datasets = {
            "123": {"source": "openml", "type": "time_perception"}
        }

        success = update_readme(readme_path, exclusion_log, verified_datasets)

        assert success
        updated_content = readme_path.read_text()
        assert "### Dataset Status" in updated_content
        assert "openml_123: excluded (reason: Missing columns)" in updated_content

    def test_update_readme_adds_section(self, tmp_path):
        """Test updating README adds status section if missing."""
        readme_path = tmp_path / "README.md"
        readme_content = """
        # Data Directory

        ## Verified datasets
        - id: 123
          source: openml
          type: time_perception
        """
        readme_path.write_text(readme_content)

        exclusion_log = []
        verified_datasets = {
            "123": {"source": "openml", "type": "time_perception"}
        }

        success = update_readme(readme_path, exclusion_log, verified_datasets)

        assert success
        updated_content = readme_path.read_text()
        assert "### Dataset Status" in updated_content
        assert "openml_123: valid" in updated_content

    def test_update_nonexistent_readme(self, tmp_path):
        """Test updating a non-existent README fails."""
        readme_path = tmp_path / "nonexistent.md"

        exclusion_log = []
        verified_datasets = {}

        success = update_readme(readme_path, exclusion_log, verified_datasets)

        assert not success


class TestRunT013:
    @patch('code.update_readme.get_data_dir')
    @patch('code.update_readme.get_processed_dir')
    def test_run_success(self, mock_processed_dir, mock_data_dir, tmp_path):
        """Test successful execution of T013."""
        # Setup mocks
        mock_data_dir.return_value = tmp_path
        mock_processed_dir.return_value = tmp_path / 'processed'
        (tmp_path / 'processed').mkdir()

        # Create test files
        exclusion_log_path = tmp_path / 'processed' / 'exclusion_log.json'
        exclusion_log_path.write_text(json.dumps([{"dataset_id": "123", "reason": "Test"}]))

        readme_path = tmp_path / 'README.md'
        readme_path.write_text("""
        # Data Directory
        ## Verified datasets
        - id: 123
          source: openml
          type: time_perception
        """)

        success = run_t013()

        assert success
        assert readme_path.exists()
        content = readme_path.read_text()
        assert "### Dataset Status" in content

    @patch('code.update_readme.get_data_dir')
    @patch('code.update_readme.get_processed_dir')
    def test_run_no_exclusion_log(self, mock_processed_dir, mock_data_dir, tmp_path):
        """Test execution with missing exclusion log (should succeed with empty log)."""
        # Setup mocks
        mock_data_dir.return_value = tmp_path
        mock_processed_dir.return_value = tmp_path / 'processed'
        (tmp_path / 'processed').mkdir()

        # Create README only
        readme_path = tmp_path / 'README.md'
        readme_path.write_text("""
        # Data Directory
        ## Verified datasets
        - id: 123
          source: openml
          type: time_perception
        """)

        success = run_t013()

        assert success
        assert readme_path.exists()
        content = readme_path.read_text()
        assert "### Dataset Status" in content