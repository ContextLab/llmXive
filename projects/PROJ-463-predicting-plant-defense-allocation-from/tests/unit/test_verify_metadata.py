"""
Unit tests for metadata verification functionality.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

from src.data.verify_metadata import (
    fetch_sra_metadata,
    extract_required_metadata,
    verify_metadata_requirements,
    verify_fastq_metadata,
    main
)
from src.utils.schemas import RNASeqStudy


class TestExtractRequiredMetadata:
    """Tests for extract_required_metadata function."""
    
    def test_extract_with_complete_metadata(self):
        """Test extraction when all required fields are present."""
        sra_metadata = {
            "accession": "SRX123456",
            "organism": "Arabidopsis thaliana",
            "platform": {
                "organism": "Arabidopsis thaliana",
                "attributes": [
                    {"tag": "Tissue", "value": "leaf"},
                    {"tag": "Treatment", "value": "caterpillar"},
                    {"tag": "Replicate", "value": "3"}
                ]
            }
        }
        
        result = extract_required_metadata(sra_metadata)
        
        assert result["species"] == "Arabidopsis thaliana"
        assert result["tissue"] == "leaf"
        assert result["herbivore_type"] == "caterpillar"
        assert result["replicates"] == 3
        assert result["accession_id"] == "SRX123456"
    
    def test_extract_with_missing_fields(self):
        """Test extraction when some fields are missing."""
        sra_metadata = {
            "accession": "SRX789012",
            "platform": {
                "attributes": [
                    {"tag": "Tissue", "value": "root"}
                ]
            }
        }
        
        result = extract_required_metadata(sra_metadata)
        
        assert result["species"] == "unknown"
        assert result["tissue"] == "root"
        assert result["herbivore_type"] == "unknown"
        assert result["replicates"] == 0
    
    def test_extract_with_alternative_organism(self):
        """Test extraction using alternative organism field."""
        sra_metadata = {
            "accession": "SRX345678",
            "organism": "Zea mays",
            "platform": {}
        }
        
        result = extract_required_metadata(sra_metadata)
        
        assert result["species"] == "Zea mays"
    
    def test_extract_with_sample_attributes(self):
        """Test extraction from sample attributes."""
        sra_metadata = {
            "accession": "SRX901234",
            "sample": {
                "attributes": [
                    {"tag": "tissue_type", "value": "stem"}
                ]
            }
        }
        
        result = extract_required_metadata(sra_metadata)
        
        assert result["tissue"] == "stem"


class TestVerifyMetadataRequirements:
    """Tests for verify_metadata_requirements function."""
    
    def test_valid_metadata(self):
        """Test validation with complete metadata."""
        metadata = {
            "tissue": "leaf",
            "herbivore_type": "caterpillar",
            "replicates": 3,
            "species": "Arabidopsis thaliana"
        }
        
        is_valid, reasons = verify_metadata_requirements(metadata)
        
        assert is_valid is True
        assert len(reasons) == 0
    
    def test_missing_tissue(self):
        """Test validation with missing tissue."""
        metadata = {
            "tissue": "unknown",
            "herbivore_type": "caterpillar",
            "replicates": 3,
            "species": "Arabidopsis thaliana"
        }
        
        is_valid, reasons = verify_metadata_requirements(metadata)
        
        assert is_valid is False
        assert "Missing or unknown tissue type" in reasons
    
    def test_missing_herbivore_type(self):
        """Test validation with missing herbivore type."""
        metadata = {
            "tissue": "leaf",
            "herbivore_type": "unknown",
            "replicates": 3,
            "species": "Arabidopsis thaliana"
        }
        
        is_valid, reasons = verify_metadata_requirements(metadata)
        
        assert is_valid is False
        assert "Missing or unknown herbivore type" in reasons
    
    def test_insufficient_replicates(self):
        """Test validation with insufficient replicates."""
        metadata = {
            "tissue": "leaf",
            "herbivore_type": "caterpillar",
            "replicates": 1,
            "species": "Arabidopsis thaliana"
        }
        
        is_valid, reasons = verify_metadata_requirements(metadata)
        
        assert is_valid is False
        assert "Insufficient biological replicates" in reasons[0]
    
    def test_multiple_failures(self):
        """Test validation with multiple failures."""
        metadata = {
            "tissue": "unknown",
            "herbivore_type": "unknown",
            "replicates": 1,
            "species": "unknown"
        }
        
        is_valid, reasons = verify_metadata_requirements(metadata)
        
        assert is_valid is False
        assert len(reasons) == 4  # All four checks fail


class TestVerifyFastqMetadata:
    """Tests for verify_fastq_metadata function."""
    
    def test_verify_synthetic_mode(self):
        """Test verification in synthetic mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fastq_path = Path(tmpdir) / "SYNTH_001.fastq.gz"
            fastq_path.touch()
            
            result = verify_fastq_metadata(fastq_path, mode="synthetic")
            
            assert "accession_id" in result
            assert "metadata" in result
            assert "exclusion_reasons" in result
            assert "verified_at" in result
            # Synthetic data should be valid by default
            assert result["is_valid"] is True
    
    def test_verify_real_mode_fetch_failure(self):
        """Test verification in real mode when fetch fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fastq_path = Path(tmpdir) / "SRX123456.fastq.gz"
            fastq_path.touch()
            
            with patch('src.data.verify_metadata.fetch_sra_metadata', return_value=None):
                result = verify_fastq_metadata(fastq_path, mode="real")
            
            assert result["is_valid"] is False
            assert "Failed to fetch metadata from NCBI" in result["exclusion_reasons"]
    
    def test_verify_real_mode_success(self):
        """Test verification in real mode with successful fetch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fastq_path = Path(tmpdir) / "SRX123456.fastq.gz"
            fastq_path.touch()
            
            mock_metadata = {
                "accession": "SRX123456",
                "organism": "Arabidopsis thaliana",
                "platform": {
                    "organism": "Arabidopsis thaliana",
                    "attributes": [
                        {"tag": "Tissue", "value": "leaf"},
                        {"tag": "Treatment", "value": "caterpillar"},
                        {"tag": "Replicate", "value": "3"}
                    ]
                }
            }
            
            with patch('src.data.verify_metadata.fetch_sra_metadata', return_value=mock_metadata):
                result = verify_fastq_metadata(fastq_path, mode="real")
            
            assert result["is_valid"] is True
            assert result["metadata"]["species"] == "Arabidopsis thaliana"
            assert result["metadata"]["tissue"] == "leaf"
            assert result["metadata"]["herbivore_type"] == "caterpillar"


class TestMain:
    """Tests for main function."""
    
    def test_main_synthetic_mode(self):
        """Test main function in synthetic mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "report.json"
            input_dir = Path(tmpdir) / "synthetic"
            input_dir.mkdir()
            
            # Create a synthetic FASTQ file
            fastq_file = input_dir / "SYNTH_001.fastq.gz"
            fastq_file.touch()
            
            with patch('sys.argv', ['verify_metadata', '--mode', 'synthetic', 
                                    '--input-dir', str(input_dir),
                                    '--output-file', str(output_file)]):
                result = main()
            
            assert output_file.exists()
            assert result["mode"] == "synthetic"
            assert result["total_files"] == 1
            assert result["valid_files"] == 1
            
            # Verify report structure
            with open(output_file) as f:
                report = json.load(f)
                assert "verification_results" in report
                assert "generated_at" in report
    
    def test_main_real_mode_with_invalid_files(self):
        """Test main function exits when invalid files found in real mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "report.json"
            input_dir = Path(tmpdir) / "raw"
            input_dir.mkdir()
            
            # Create a FASTQ file
            fastq_file = input_dir / "SRX123456.fastq.gz"
            fastq_file.touch()
            
            # Mock fetch to return invalid metadata
            mock_metadata = {
                "accession": "SRX123456",
                "platform": {
                    "attributes": [
                        {"tag": "Tissue", "value": "unknown"},
                        {"tag": "Treatment", "value": "unknown"},
                        {"tag": "Replicate", "value": "1"}
                    ]
                }
            }
            
            with patch('sys.argv', ['verify_metadata', '--mode', 'real',
                                    '--input-dir', str(input_dir),
                                    '--output-file', str(output_file)]):
                with patch('src.data.verify_metadata.fetch_sra_metadata', return_value=mock_metadata):
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    
                    assert exc_info.value.code == 1
            
            # Report should still be written
            assert output_file.exists()
            
            with open(output_file) as f:
                report = json.load(f)
                assert report["invalid_files"] > 0