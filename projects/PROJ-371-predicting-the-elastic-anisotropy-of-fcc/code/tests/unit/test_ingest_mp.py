"""
Unit tests for Materials Project ingestion module (T012a).
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.ingest_mp import (
    load_manifest,
    fetch_elastic_constants_mp,
    ingest_elastic_data,
)
from src.utils.config import get_config

class TestLoadManifest:
    def test_load_manifest_success(self, tmp_path):
        """Test successful loading of a valid manifest."""
        manifest_data = {"material_ids": ["mp-13", "mp-11", "mp-15"]}
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(manifest_data))

        result = load_manifest(manifest_file)
        assert result == ["mp-13", "mp-11", "mp-15"]

    def test_load_manifest_missing_key(self, tmp_path):
        """Test that missing 'material_ids' key raises ValueError."""
        manifest_data = {"other_key": ["mp-13"]}
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(manifest_data))

        with pytest.raises(ValueError, match="must contain 'material_ids'"):
            load_manifest(manifest_file)

    def test_load_manifest_not_list(self, tmp_path):
        """Test that non-list material_ids raises ValueError."""
        manifest_data = {"material_ids": "mp-13"}
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(manifest_data))

        with pytest.raises(ValueError, match="must be a list"):
            load_manifest(manifest_file)

    def test_load_manifest_file_not_found(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_manifest(Path("/nonexistent/path/manifest.json"))

    def test_load_manifest_invalid_json(self, tmp_path):
        """Test that invalid JSON raises JSONDecodeError."""
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text("not valid json {")

        with pytest.raises(json.JSONDecodeError):
            load_manifest(manifest_file)

class TestFetchElasticConstants:
    @patch("src.data.ingest_mp.requests.Session")
    def test_fetch_success(self, mock_session_class, monkeypatch):
        """Test successful fetch of elastic constants."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "elasticity": {
                    "elastic_tensor": [
                        [106.0, 60.0, 60.0, 0, 0, 0],
                        [60.0, 106.0, 60.0, 0, 0, 0],
                        [60.0, 60.0, 106.0, 0, 0, 0],
                        [0, 0, 0, 28.0, 0, 0],
                        [0, 0, 0, 0, 28.0, 0],
                        [0, 0, 0, 0, 0, 28.0],
                    ]
                }
            }
        }
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = fetch_elastic_constants_mp("mp-13", "fake_api_key")

        assert result is not None
        assert result["material_id"] == "mp-13"
        assert result["C11"] == 106.0
        assert result["C12"] == 60.0
        assert result["C44"] == 28.0

    @patch("src.data.ingest_mp.requests.Session")
    def test_fetch_missing_data_key(self, mock_session_class, monkeypatch):
        """Test handling of response missing 'data' key."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"error": "Not found"}
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = fetch_elastic_constants_mp("mp-999", "fake_api_key")
        assert result is None

    @patch("src.data.ingest_mp.requests.Session")
    def test_fetch_invalid_tensor(self, mock_session_class, monkeypatch):
        """Test handling of invalid elastic tensor."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": {"elasticity": {"elastic_tensor": [[1]]}}
        }
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = fetch_elastic_constants_mp("mp-13", "fake_api_key")
        assert result is None

    @patch("src.data.ingest_mp.requests.Session")
    def test_fetch_request_exception(self, mock_session_class, monkeypatch):
        """Test handling of request exceptions."""
        import requests

        mock_session = MagicMock()
        mock_session.get.side_effect = requests.exceptions.Timeout()
        mock_session_class.return_value = mock_session

        result = fetch_elastic_constants_mp("mp-13", "fake_api_key")
        assert result is None

class TestIngestElasticData:
    def test_ingest_test_mode(self, tmp_path):
        """Test ingestion in test mode loads static fixtures."""
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps({"material_ids": ["mp-13"]}))

        output_file = tmp_path / "output.csv"

        df = ingest_elastic_data(
            manifest_path=manifest_file, output_path=output_file, test_mode=True
        )

        assert len(df) > 0
        assert "material_id" in df.columns
        assert "C11" in df.columns
        assert "C12" in df.columns
        assert "C44" in df.columns
        assert output_file.exists()

    def test_ingest_missing_api_key_raises(self, tmp_path, monkeypatch):
        """Test that missing API key raises ValueError (not in test mode)."""
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps({"material_ids": ["mp-13"]}))

        # Ensure no API key is set
        monkeypatch.delenv("MP_API_KEY", raising=False)

        with pytest.raises(ValueError, match="API key not found"):
            ingest_elastic_data(
                manifest_path=manifest_file,
                output_path=tmp_path / "output.csv",
                test_mode=False,
            )

    def test_ingest_manifest_not_found_raises(self):
        """Test that missing manifest raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            ingest_elastic_data(
                manifest_path=Path("/nonexistent/manifest.json"),
                test_mode=False,
            )

    def test_ingest_creates_output_directory(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps({"material_ids": ["mp-13"]}))

        output_dir = tmp_path / "deep" / "nested" / "output"
        output_file = output_dir / "results.csv"

        df = ingest_elastic_data(
            manifest_path=manifest_file,
            output_path=output_file,
            test_mode=True,
        )

        assert output_file.exists()