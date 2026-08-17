"""
Tests for the PMD CLI Wrapper Script (T014b).

These tests verify that the wrapper script correctly loads file lists,
handles errors, and invokes the underlying PMD logic.
"""

import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure the project root is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wrapper_pmd import load_file_list, save_results, main


class TestWrapperPmd:

    @pytest.fixture
    def temp_input_file(self, tmp_path):
        """Create a temporary input JSON file."""
        input_file = tmp_path / "files.json"
        files = [
            "/path/to/valid/File1.java",
            "/path/to/valid/File2.java"
        ]
        with open(input_file, 'w') as f:
            json.dump(files, f)
        return str(input_file)

    @pytest.fixture
    def temp_output_file(self, tmp_path):
        """Create a temporary output file path."""
        return str(tmp_path / "results.json")

    def test_load_file_list_valid(self, temp_input_file):
        """Test loading a valid JSON file list."""
        result = load_file_list(temp_input_file)
        assert len(result) == 2
        assert result[0] == "/path/to/valid/File1.java"

    def test_load_file_list_dict_format(self, tmp_path):
        """Test loading a JSON file list in dict format."""
        input_file = tmp_path / "files_dict.json"
        data = {"files": ["/path/to/File3.java"]}
        with open(input_file, 'w') as f:
            json.dump(data, f)

        result = load_file_list(str(input_file))
        assert len(result) == 1
        assert result[0] == "/path/to/File3.java"

    def test_load_file_list_missing_file(self, tmp_path):
        """Test error handling when input file is missing."""
        with pytest.raises(FileNotFoundError):
            load_file_list(str(tmp_path / "nonexistent.json"))

    def test_load_file_list_invalid_json(self, tmp_path):
        """Test error handling for invalid JSON structure."""
        input_file = tmp_path / "invalid.json"
        with open(input_file, 'w') as f:
            f.write("not a list or dict")

        with pytest.raises(ValueError):
            load_file_list(str(input_file))

    def test_save_results(self, tmp_path):
        """Test saving results to a JSON file."""
        output_path = str(tmp_path / "output.json")
        results = [
            {"file": "/path/to/File1.java", "cc": 5},
            {"file": "/path/to/File2.java", "cc": 10}
        ]

        save_results(output_path, results)

        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            loaded = json.load(f)

        assert loaded == results

    @patch('wrapper_pmd.calculate_cc_batch')
    @patch('wrapper_pmd.get_pmd_path')
    def test_main_execution_success(self, mock_get_pmd, mock_calc_batch, temp_input_file, temp_output_file, tmp_path):
        """Test the main function execution path."""
        # Mock PMD path
        mock_get_pmd.return_value = "/usr/bin/pmd"
        mock_calc_batch.return_value = [
            {"file": "/path/to/valid/File1.java", "cc": 5},
            {"file": "/path/to/valid/File2.java", "cc": 10}
        ]

        # Mock sys.argv to simulate command line arguments
        test_args = [
            'wrapper_pmd.py',
            '--input', temp_input_file,
            '--output', temp_output_file
        ]

        with patch.object(sys, 'argv', test_args):
            main()

        # Verify output file was created
        assert os.path.exists(temp_output_file)
        mock_calc_batch.assert_called_once()

    @patch('wrapper_pmd.get_pmd_path')
    def test_main_pmd_not_found(self, mock_get_pmd, temp_input_file, tmp_path):
        """Test main function when PMD is not found."""
        mock_get_pmd.return_value = None
        output_file = str(tmp_path / "out.json")

        test_args = [
            'wrapper_pmd.py',
            '--input', temp_input_file,
            '--output', output_file
        ]

        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1