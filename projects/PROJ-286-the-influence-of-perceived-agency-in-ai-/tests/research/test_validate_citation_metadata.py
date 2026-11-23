"""
Tests for code/research/validate_citation_metadata.py (T000b)
"""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path for imports if running from tests directory
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.research.validate_citation_metadata import (
    load_json_file,
    fetch_crossref_metadata,
    validate_metadata,
    main,
    LEE_SEE_2004_DOI,
    EXPECTED_YEAR,
    EXPECTED_JOURNAL_KEYWORDS
)


class TestLoadJsonFile:
    def test_load_json_file_valid(self, tmp_path):
        data = {"key": "value"}
        file_path = tmp_path / "test.json"
        file_path.write_text(json.dumps(data))

        result = load_json_file(file_path)
        assert result == data

    def test_load_json_file_not_found(self, tmp_path):
        non_existent = tmp_path / "non_existent.json"
        with pytest.raises(SystemExit):
            load_json_file(non_existent)

    def test_load_json_file_invalid(self, tmp_path):
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not json")
        with pytest.raises(SystemExit):
            load_json_file(file_path)


class TestFetchCrossrefMetadata:
    @patch('code.research.validate_citation_metadata.requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"message": {"DOI": "10.123/test"}}
        mock_get.return_value = mock_response

        result = fetch_crossref_metadata("10.123/test")
        assert result["message"]["DOI"] == "10.123/test"
        mock_get.assert_called_once()

    @patch('code.research.validate_citation_metadata.requests.get')
    def test_fetch_request_exception(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        with pytest.raises(SystemExit):
            fetch_crossref_metadata("10.123/test")


class TestValidateMetadata:
    def test_validate_metadata_match(self):
        mock_data = {
            "message": {
                "DOI": LEE_SEE_2004_DOI,
                "title": ["Trust in Automation"],
                "published-print": {"date-parts": [[2004]]},
                "container-title": ["Human Factors"]
            }
        }
        result = validate_metadata(mock_data, 2004, ["Human Factors"])
        assert result["status"] == "verified"
        assert result["year_match"] is True
        assert result["journal_match"] is True

    def test_validate_metadata_year_mismatch(self):
        mock_data = {
            "message": {
                "DOI": LEE_SEE_2004_DOI,
                "title": ["Trust in Automation"],
                "published-print": {"date-parts": [[2005]]},
                "container-title": ["Human Factors"]
            }
        }
        result = validate_metadata(mock_data, 2004, ["Human Factors"])
        assert result["status"] == "mismatch"
        assert result["year_match"] is False

    def test_validate_metadata_journal_mismatch(self):
        mock_data = {
            "message": {
                "DOI": LEE_SEE_2004_DOI,
                "title": ["Trust in Automation"],
                "published-print": {"date-parts": [[2004]]},
                "container-title": ["Some Other Journal"]
            }
        }
        result = validate_metadata(mock_data, 2004, ["Human Factors"])
        assert result["status"] == "mismatch"
        assert result["journal_match"] is False


class TestMain:
    @patch('code.research.validate_citation_metadata.fetch_crossref_metadata')
    @patch('code.research.validate_citation_metadata.validate_metadata')
    @patch('code.research.validate_citation_metadata.OUTPUT_PATH')
    def test_main_success(self, mock_output_path, mock_validate, mock_fetch, tmp_path):
        # Setup mock paths
        mock_output_path.parent = tmp_path
        mock_output_path.__truediv__ = lambda self, name: tmp_path / name
        
        # Mock input file
        input_data = {"status": "ok"}
        input_path = Path(__file__).parent.parent.parent / "research" / "validation_report.json"
        # Ensure the directory exists for the real path check if needed, 
        # but here we mock the existence check logic inside main by ensuring the file exists
        # or by patching the path check. Since main checks VALIDATION_REPORT_PATH directly:
        # We need to ensure the file exists at the expected location or patch the path check.
        # For this unit test, we will create the file at the expected location relative to the repo root 
        # which is tricky without knowing the exact repo root in CI. 
        # Instead, we patch the VALIDATION_REPORT_PATH check.
        
        real_validation_path = Path(__file__).parent.parent.parent.parent / "research" / "validation_report.json"
        real_validation_path.parent.mkdir(parents=True, exist_ok=True)
        real_validation_path.write_text(json.dumps(input_data))

        mock_fetch.return_value = {"message": {"DOI": "10.123"}}
        mock_validate.return_value = {"status": "verified", "year": 2004, "journal": "Human Factors", "title": "Test"}

        main()

        # Check output file created
        assert mock_output_path.exists()
        with open(mock_output_path, 'r') as f:
            output_data = json.load(f)
        assert output_data["status"] == "verified"
        
        # Cleanup
        real_validation_path.unlink()

    @patch('code.research.validate_citation_metadata.fetch_crossref_metadata')
    @patch('code.research.validate_citation_metadata.validate_metadata')
    def test_main_metadata_mismatch(self, mock_validate, mock_fetch, tmp_path):
        mock_fetch.return_value = {"message": {"DOI": "10.123"}}
        mock_validate.return_value = {"status": "mismatch", "year": 2005, "journal": "Other", "title": "Test"}
        
        # Create dummy input file
        real_validation_path = Path(__file__).parent.parent.parent.parent / "research" / "validation_report.json"
        real_validation_path.parent.mkdir(parents=True, exist_ok=True)
        real_validation_path.write_text(json.dumps({"status": "ok"}))

        with pytest.raises(SystemExit):
            main()
        
        # Cleanup
        real_validation_path.unlink()

    def test_main_missing_input_file(self, tmp_path):
        # Ensure the input file does not exist
        real_validation_path = Path(__file__).parent.parent.parent.parent / "research" / "validation_report.json"
        if real_validation_path.exists():
            real_validation_path.unlink()
        
        with pytest.raises(SystemExit):
            main()