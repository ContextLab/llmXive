"""
Unit tests for Gate 0 validation logic.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

from gate0 import (
    DataNotFoundError,
    parse_verified_datasets_block,
    validate_gate0,
    update_readme_with_gate_status,
    main
)


class TestParseVerifiedDatasetsBlock:
    def test_parse_valid_block(self):
        readme_content = """
        # Data Directory

        ### Verified datasets
        - id: 42277
          source: openml
          type: time_perception
        - id: 42278
          source: openml
          type: time_perception

        ## Exclusion Logs
        """
        datasets = parse_verified_datasets_block(readme_content)

        assert len(datasets) == 2
        assert datasets[0]['id'] == 42277
        assert datasets[0]['source'] == 'openml'
        assert datasets[0]['type'] == 'time_perception'
        assert datasets[1]['id'] == 42278

    def test_parse_empty_block(self):
        readme_content = """
        # Data Directory

        ### Verified datasets

        ## Exclusion Logs
        """
        datasets = parse_verified_datasets_block(readme_content)
        assert datasets == []

    def test_parse_no_block(self):
        readme_content = """
        # Data Directory

        ## Exclusion Logs
        """
        datasets = parse_verified_datasets_block(readme_content)
        assert datasets == []


class TestValidateGate0:
    def test_valid_datasets(self):
        datasets = [
            {'id': 42277, 'source': 'openml', 'type': 'time_perception'},
            {'id': 42278, 'source': 'huggingface', 'type': 'time_perception'}
        ]
        assert validate_gate0(datasets) is True

    def test_empty_datasets_raises(self):
        with pytest.raises(DataNotFoundError, match="No verified datasets found"):
            validate_gate0([])

    def test_missing_keys_raises(self):
        datasets = [{'id': 42277, 'source': 'openml'}]
        with pytest.raises(DataNotFoundError, match="missing required keys"):
            validate_gate0(datasets)

    def test_invalid_id_type_raises(self):
        datasets = [{'id': 'not_an_int', 'source': 'openml', 'type': 'time_perception'}]
        with pytest.raises(DataNotFoundError, match="id must be an integer"):
            validate_gate0(datasets)

    def test_invalid_source_raises(self):
        datasets = [{'id': 42277, 'source': 'invalid_source', 'type': 'time_perception'}]
        with pytest.raises(DataNotFoundError, match="Invalid source"):
            validate_gate0(datasets)

    def test_invalid_type_raises(self):
        datasets = [{'id': 42277, 'source': 'openml', 'type': 'invalid_type'}]
        with pytest.raises(DataNotFoundError, match="Invalid type"):
            validate_gate0(datasets)


class TestUpdateReadmeWithGateStatus:
    def test_add_new_status(self, tmp_path):
        readme_path = tmp_path / 'README.md'
        readme_path.write_text("# Data Directory\n")

        update_readme_with_gate_status(readme_path, "Gate 0: Passed")

        content = readme_path.read_text()
        assert "## Gate 0 Status" in content
        assert "Gate 0: Passed" in content

    def test_update_existing_status(self, tmp_path):
        readme_path = tmp_path / 'README.md'
        readme_path.write_text(
            "# Data Directory\n\n## Gate 0 Status\nGate 0: Failed\n"
        )

        update_readme_with_gate_status(readme_path, "Gate 0: Passed")

        content = readme_path.read_text()
        assert content.count("## Gate 0 Status") == 1
        assert "Gate 0: Passed" in content
        assert "Gate 0: Failed" not in content


class TestMain:
    @patch('gate0.get_data_dir')
    def test_main_success(self, mock_get_data_dir, tmp_path):
        # Setup mock
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        readme_path = data_dir / 'README.md'
        readme_path.write_text(
            "# Data Directory\n\n### Verified datasets\n- id: 42277\n  source: openml\n  type: time_perception\n"
        )
        mock_get_data_dir.return_value = data_dir

        result = main()

        assert result == 0
        assert "Gate 0: Passed" in readme_path.read_text()

    @patch('gate0.get_data_dir')
    def test_main_no_datasets(self, mock_get_data_dir, tmp_path):
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        readme_path = data_dir / 'README.md'
        readme_path.write_text("# Data Directory\n")
        mock_get_data_dir.return_value = data_dir

        result = main()

        assert result == 1
        assert "Gate 0: Passed" not in readme_path.read_text()

    @patch('gate0.get_data_dir')
    def test_main_file_not_found(self, mock_get_data_dir, tmp_path):
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        mock_get_data_dir.return_value = data_dir

        result = main()

        assert result == 1