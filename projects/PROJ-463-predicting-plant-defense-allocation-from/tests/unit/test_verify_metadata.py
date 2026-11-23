"""
Unit tests for metadata verification module.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.data.verify_metadata import (
    fetch_sra_metadata,
    extract_required_metadata,
    verify_metadata_requirements,
    verify_fastq_metadata
)


class TestExtractRequiredMetadata:
    def test_extract_all_fields(self):
        """Test extraction when all fields are present."""
        metadata = {
            "tissue": "leaf",
            "treatment": "herbivore",
            "replicates": 3,
            "species": "Arabidopsis thaliana"
        }
        
        result = extract_required_metadata(metadata)
        
        assert result["tissue"] == "leaf"
        assert result["treatment"] == "herbivore"
        assert result["replicates"] == 3
        assert result["species"] == "Arabidopsis thaliana"

    def test_extract_missing_fields(self):
        """Test extraction when some fields are missing."""
        metadata = {
            "tissue": "leaf",
            "species": "Arabidopsis thaliana"
        }
        
        result = extract_required_metadata(metadata)
        
        assert result["tissue"] == "leaf"
        assert result["treatment"] is None
        assert result["replicates"] is None
        assert result["species"] == "Arabidopsis thaliana"


class TestVerifyMetadataRequirements:
    def test_all_requirements_met(self):
        """Test when all requirements are met."""
        metadata = {
            "tissue": "leaf",
            "treatment": "herbivore",
            "replicates": 3,
            "species": "Arabidopsis thaliana"
        }
        
        is_valid, reasons = verify_metadata_requirements(metadata, "SRR123456")
        
        assert is_valid is True
        assert len(reasons) == 0

    def test_missing_tissue(self):
        """Test when tissue is missing."""
        metadata = {
            "treatment": "herbivore",
            "replicates": 3,
            "species": "Arabidopsis thaliana"
        }
        
        is_valid, reasons = verify_metadata_requirements(metadata, "SRR123456")
        
        assert is_valid is False
        assert any("tissue" in reason for reason in reasons)

    def test_insufficient_replicates(self):
        """Test when replicates are insufficient."""
        metadata = {
            "tissue": "leaf",
            "treatment": "herbivore",
            "replicates": 1,
            "species": "Arabidopsis thaliana"
        }
        
        is_valid, reasons = verify_metadata_requirements(metadata, "SRR123456")
        
        assert is_valid is False
        assert any("replicates" in reason for reason in reasons)

    def test_missing_all_fields(self):
        """Test when all required fields are missing."""
        metadata = {}
        
        is_valid, reasons = verify_metadata_requirements(metadata, "SRR123456")
        
        assert is_valid is False
        assert len(reasons) == 4  # tissue, treatment, replicates, species


class TestVerifyFastqMetadata:
    @patch('src.data.verify_metadata.fetch_sra_metadata')
    def test_verify_with_mocked_fetch(self, mock_fetch):
        """Test verification with mocked metadata fetch."""
        # Setup mock
        mock_fetch.return_value = {
            "accession_id": "SRR123456",
            "tissue": "leaf",
            "treatment": "herbivore",
            "replicates": 3,
            "species": "Arabidopsis thaliana"
        }
        
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_path = Path(tmpdir) / "raw"
            raw_path.mkdir()
            
            # Create a fake FASTQ file
            fastq_file = raw_path / "SRR123456.fastq.gz"
            fastq_file.touch()
            
            # Run verification
            report = verify_fastq_metadata([fastq_file])
            
            assert report["total_studies"] == 1
            assert len(report["passed"]) == 1
            assert len(report["failed"]) == 0
            assert len(report["excluded"]) == 0

    @patch('src.data.verify_metadata.fetch_sra_metadata')
    def test_verify_with_failed_fetch(self, mock_fetch):
        """Test verification when metadata fetch fails."""
        mock_fetch.return_value = None
        
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_path = Path(tmpdir) / "raw"
            raw_path.mkdir()
            
            fastq_file = raw_path / "SRR123456.fastq.gz"
            fastq_file.touch()
            
            report = verify_fastq_metadata([fastq_file])
            
            assert report["total_studies"] == 1
            assert len(report["passed"]) == 0
            assert len(report["failed"]) == 1
            assert len(report["excluded"]) == 0

    @patch('src.data.verify_metadata.fetch_sra_metadata')
    def test_verify_with_insufficient_replicates(self, mock_fetch):
        """Test verification when replicates are insufficient."""
        mock_fetch.return_value = {
            "accession_id": "SRR123456",
            "tissue": "leaf",
            "treatment": "herbivore",
            "replicates": 1,  # Insufficient
            "species": "Arabidopsis thaliana"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_path = Path(tmpdir) / "raw"
            raw_path.mkdir()
            
            fastq_file = raw_path / "SRR123456.fastq.gz"
            fastq_file.touch()
            
            report = verify_fastq_metadata([fastq_file])
            
            assert report["total_studies"] == 1
            assert len(report["passed"]) == 0
            assert len(report["failed"]) == 0
            assert len(report["excluded"]) == 1
            assert "replicates" in report["excluded"][0]["exclusion_reasons"][0]