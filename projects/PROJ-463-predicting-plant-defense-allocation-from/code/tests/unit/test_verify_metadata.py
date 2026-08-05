"""
Unit tests for metadata verification (T011a).
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.verify_metadata import (
    fetch_sra_metadata,
    extract_required_metadata,
    verify_metadata_requirements,
    verify_fastq_metadata,
    verify_synthetic_metadata,
    save_verification_report,
    calculate_sha256
)


class TestVerifyMetadata:
    """Test cases for metadata verification functions."""

    def test_calculate_sha256(self):
        """Test SHA256 calculation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = Path(tmp.name)

        checksum = calculate_sha256(tmp_path)
        assert len(checksum) == 64  # SHA256 hex length
        assert checksum == "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"

        tmp_path.unlink()

    def test_extract_required_metadata(self):
        """Test metadata extraction from file path."""
        with tempfile.NamedTemporaryFile(suffix=".fastq.gz", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        metadata = extract_required_metadata(tmp_path)
        assert "file_path" in metadata
        assert metadata["file_path"] == str(tmp_path)
        assert metadata["checksum"] is not None

        tmp_path.unlink()

    def test_verify_metadata_requirements_valid(self):
        """Test verification with valid metadata."""
        metadata = {
            "species": "Arabidopsis thaliana",
            "tissue": "leaf",
            "treatment": "chewing",
            "replicates": 3
        }

        is_valid, issues = verify_metadata_requirements(metadata)
        assert is_valid
        assert len(issues) == 0

    def test_verify_metadata_requirements_missing_species(self):
        """Test verification with missing species."""
        metadata = {
            "tissue": "leaf",
            "treatment": "chewing",
            "replicates": 3
        }

        is_valid, issues = verify_metadata_requirements(metadata)
        assert not is_valid
        assert "Missing species information" in issues

    def test_verify_metadata_requirements_insufficient_replicates(self):
        """Test verification with insufficient replicates."""
        metadata = {
            "species": "Arabidopsis thaliana",
            "tissue": "leaf",
            "treatment": "chewing",
            "replicates": 1
        }

        is_valid, issues = verify_metadata_requirements(metadata)
        assert not is_valid
        assert any("Insufficient replicates" in issue for issue in issues)

    @patch('src.data.verify_metadata.requests.get')
    def test_fetch_sra_metadata_success(self, mock_get):
        """Test successful metadata fetch from SRA."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "esearchresult": {
                "idlist": ["12345"]
            }
        }
        mock_response2 = MagicMock()
        mock_response2.json.return_value = {
            "result": {
                "12345": {
                    "organism": "Arabidopsis thaliana",
                    "description": "chewing herbivory treatment",
                    "attributes": [
                        {"attribute_name": "organ", "attribute_value": "leaf"}
                    ]
                }
            }
        }

        mock_get.side_effect = [mock_response, mock_response2]

        metadata = fetch_sra_metadata("SRR12345")

        assert metadata is not None
        assert metadata["species"] == "Arabidopsis thaliana"
        assert metadata["tissue"] == "leaf"

    def test_verify_synthetic_metadata_existing(self):
        """Test verification of existing synthetic manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "synthetic_manifest.json"
            manifest_data = {
                "accession_id": "SYNTH_001",
                "source_type": "synthetic"
            }
            with open(manifest_path, 'w') as f:
                json.dump(manifest_data, f)

            result = verify_synthetic_metadata(manifest_path)
            assert result["status"] == "valid"
            assert result["mode"] == "synthetic"

    def test_verify_synthetic_metadata_missing(self):
        """Test verification of missing synthetic manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "nonexistent.json"

            result = verify_synthetic_metadata(manifest_path)
            assert result["status"] == "error"
            assert "not found" in result["message"].lower()

    def test_save_verification_report(self):
        """Test saving verification report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            results = [
                {
                    "file": "test.fastq.gz",
                    "status": "valid",
                    "species": "Arabidopsis thaliana"
                }
            ]

            save_verification_report(results, output_path)

            assert output_path.exists()
            with open(output_path, 'r') as f:
                report = json.load(f)

            assert report["total_files"] == 1
            assert report["valid_files"] == 1