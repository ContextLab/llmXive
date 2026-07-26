"""
Unit tests for metadata verification functionality.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.verify_metadata import (
    fetch_sra_metadata,
    extract_required_metadata,
    verify_metadata_requirements,
    verify_fastq_metadata
)


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        yield Path(f.name)
    os.unlink(f.name)


@pytest.fixture
def temp_manifest():
    """Create a temporary manifest file for testing."""
    manifest = {
        "entries": [
            {
                "accession_id": "SRX123456",
                "file_name": "test.fastq.gz",
                "checksum": "abc123",
                "source_type": "real"
            }
        ]
    }
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(manifest, f)
        yield Path(f.name)
    os.unlink(f.name)


class TestExtractRequiredMetadata:
    """Test metadata extraction logic."""
    
    def test_extract_with_tissue_and_herbivore(self):
        """Test extraction when all required fields are present."""
        metadata = {
            "sample_title": "Leaf tissue treated with aphid",
            "organism": "Arabidopsis thaliana",
            "attributes": [
                {"tag": "tissue", "value": "leaf"},
                {"tag": "herbivore", "value": "aphid"}
            ],
            "runs": ["SRR1", "SRR2"]
        }
        
        result = extract_required_metadata(metadata)
        
        assert result["tissue"] == "leaf"
        assert result["herbivore_type"] == "aphid"
        assert result["replicates"] == 2
        assert result["organism"] == "Arabidopsis thaliana"
    
    def test_extract_with_inferred_tissue(self):
        """Test tissue inference from sample title."""
        metadata = {
            "sample_title": "Root tissue sample",
            "attributes": [],
            "runs": ["SRR1"]
        }
        
        result = extract_required_metadata(metadata)
        
        assert result["tissue"] == "root"
    
    def test_extract_with_default_replicates(self):
        """Test default replicates when runs not specified."""
        metadata = {
            "sample_title": "Test sample",
            "attributes": [],
            "runs": []
        }
        
        result = extract_required_metadata(metadata)
        
        assert result["replicates"] == 1


class TestVerifyMetadataRequirements:
    """Test metadata requirement validation."""
    
    def test_valid_metadata(self):
        """Test valid metadata passes all checks."""
        metadata = {
            "tissue": "leaf",
            "herbivore_type": "aphid",
            "replicates": 3
        }
        
        is_valid, reasons = verify_metadata_requirements(metadata, min_replicates=2)
        
        assert is_valid is True
        assert len(reasons) == 0
    
    def test_missing_tissue(self):
        """Test failure when tissue is missing."""
        metadata = {
            "tissue": None,
            "herbivore_type": "aphid",
            "replicates": 3
        }
        
        is_valid, reasons = verify_metadata_requirements(metadata, min_replicates=2)
        
        assert is_valid is False
        assert "Missing tissue information" in reasons
    
    def test_missing_herbivore(self):
        """Test failure when herbivore type is missing."""
        metadata = {
            "tissue": "leaf",
            "herbivore_type": None,
            "replicates": 3
        }
        
        is_valid, reasons = verify_metadata_requirements(metadata, min_replicates=2)
        
        assert is_valid is False
        assert "Missing herbivore type information" in reasons
    
    def test_insufficient_replicates(self):
        """Test failure when replicates are insufficient."""
        metadata = {
            "tissue": "leaf",
            "herbivore_type": "aphid",
            "replicates": 1
        }
        
        is_valid, reasons = verify_metadata_requirements(metadata, min_replicates=2)
        
        assert is_valid is False
        assert "Insufficient replicates" in reasons[0]


class TestVerifyFastqMetadata:
    """Test the main verification function."""
    
    def test_synthetic_mode(self, temp_manifest, temp_file):
        """Test verification in synthetic mode."""
        # Create a synthetic manifest
        manifest = {
            "entries": [
                {
                    "accession_id": "SYNTH_001",
                    "file_name": "synthetic.fastq.gz",
                    "checksum": "def456",
                    "source_type": "synthetic",
                    "provenance": {
                        "accession_id": "SYNTH_001",
                        "generated_at": "2024-01-01T00:00:00Z"
                    }
                }
            ]
        }
        
        with open(temp_manifest, 'w') as f:
            json.dump(manifest, f)
        
        report = verify_fastq_metadata(
            manifest_path=Path(temp_manifest),
            output_path=Path(temp_file),
            mode="synthetic"
        )
        
        assert report["mode"] == "synthetic"
        assert report["verified_count"] == 1
        assert report["excluded_count"] == 0
    
    def test_real_mode_with_mocked_fetch(self, temp_manifest, temp_file):
        """Test verification in real mode with mocked NCBI fetch."""
        mock_metadata = {
            "sample_title": "Leaf tissue treated with aphid",
            "organism": "Arabidopsis thaliana",
            "attributes": [
                {"tag": "tissue", "value": "leaf"},
                {"tag": "herbivore", "value": "aphid"}
            ],
            "runs": ["SRR1", "SRR2"]
        }
        
        with patch('src.data.verify_metadata.fetch_sra_metadata', return_value=mock_metadata):
            report = verify_fastq_metadata(
                manifest_path=Path(temp_manifest),
                output_path=Path(temp_file),
                mode="real"
            )
        
        assert report["mode"] == "real"
        assert report["verified_count"] == 1
        assert report["excluded_count"] == 0
    
    def test_real_mode_with_failed_fetch(self, temp_manifest, temp_file):
        """Test verification when NCBI fetch fails."""
        with patch('src.data.verify_metadata.fetch_sra_metadata', return_value=None):
            report = verify_fastq_metadata(
                manifest_path=Path(temp_manifest),
                output_path=Path(temp_file),
                mode="real"
            )
        
        assert report["excluded_count"] == 1
        assert report["verified_count"] == 0
        assert "Failed to fetch metadata" in report["excluded_studies"][0]["reason"]
    
    def test_output_file_created(self, temp_manifest, temp_file):
        """Test that output file is created."""
        mock_metadata = {
            "sample_title": "Leaf tissue treated with aphid",
            "attributes": [
                {"tag": "tissue", "value": "leaf"},
                {"tag": "herbivore", "value": "aphid"}
            ],
            "runs": ["SRR1", "SRR2"]
        }
        
        with patch('src.data.verify_metadata.fetch_sra_metadata', return_value=mock_metadata):
            verify_fastq_metadata(
                manifest_path=Path(temp_manifest),
                output_path=Path(temp_file),
                mode="real"
            )
        
        assert Path(temp_file).exists()
        
        # Verify file content
        with open(temp_file, 'r') as f:
            report = json.load(f)
        
        assert "verification_timestamp" in report
        assert "verified_studies" in report
        assert "excluded_studies" in report
