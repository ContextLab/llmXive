"""
Unit tests for metadata verification (T011a)
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.data.verify_metadata import (
    extract_required_metadata,
    verify_metadata_requirements,
    verify_fastq_metadata
)


class TestExtractRequiredMetadata:
    """Tests for metadata extraction logic"""

    def test_extract_tissue_variations(self):
        """Test extraction of tissue field with various key names"""
        test_cases = [
            ({"tissue": "leaf"}, "leaf"),
            ({"organ": "root"}, "root"),
            ({"organism_part": "stem"}, "stem"),
            ({"source": "flower"}, "flower"),
            ({}, 1)  # Default replicates
        ]

        for metadata, expected in test_cases:
            result = extract_required_metadata(metadata)
            if expected in [1] and "tissue" not in metadata:
                assert "tissue" not in result
            elif "tissue" in metadata or any(k in metadata for k in ["tissue", "organ", "organism_part", "source"]):
                assert result.get("tissue") == expected

    def test_extract_replicates_variations(self):
        """Test extraction of replicates field"""
        test_cases = [
            ({"replicates": 3}, 3),
            ({"replicate": 5}, 5),
            ({"n": 10}, 10),
            ({"sample_size": 2}, 2),
            ({"replicates": "4"}, 4),  # String to int
            ({}, 1)  # Default
        ]

        for metadata, expected in test_cases:
            result = extract_required_metadata(metadata)
            assert result.get("replicates") == expected

    def test_extract_herbivore_type(self):
        """Test extraction of herbivore type"""
        test_cases = [
            ({"herbivore": "aphid"}, "aphid"),
            ({"herbivore_type": "caterpillar"}, "caterpillar"),
            ({"treatment": "beetle"}, "beetle"),
            ({"stressor": "grasshopper"}, "grasshopper")
        ]

        for metadata, expected in test_cases:
            result = extract_required_metadata(metadata)
            assert result.get("herbivore_type") == expected


class TestVerifyMetadataRequirements:
    """Tests for metadata requirement verification"""

    def test_valid_metadata(self):
        """Test that valid metadata passes verification"""
        metadata = {
            "tissue": "leaf",
            "herbivore_type": "aphid",
            "replicates": 3
        }
        is_valid, reasons = verify_metadata_requirements(metadata)
        assert is_valid is True
        assert len(reasons) == 0

    def test_missing_tissue(self):
        """Test exclusion for missing tissue"""
        metadata = {
            "herbivore_type": "aphid",
            "replicates": 3
        }
        is_valid, reasons = verify_metadata_requirements(metadata)
        assert is_valid is False
        assert any("tissue" in r for r in reasons)

    def test_missing_herbivore_type(self):
        """Test exclusion for missing herbivore type"""
        metadata = {
            "tissue": "leaf",
            "replicates": 3
        }
        is_valid, reasons = verify_metadata_requirements(metadata)
        assert is_valid is False
        assert any("herbivore" in r for r in reasons)

    def test_insufficient_replicates(self):
        """Test exclusion for insufficient replicates"""
        metadata = {
            "tissue": "leaf",
            "herbivore_type": "aphid",
            "replicates": 1
        }
        is_valid, reasons = verify_metadata_requirements(metadata)
        assert is_valid is False
        assert any("replicates" in r for r in reasons)

    def test_empty_tissue_field(self):
        """Test exclusion for empty tissue field"""
        metadata = {
            "tissue": "",
            "herbivore_type": "aphid",
            "replicates": 3
        }
        is_valid, reasons = verify_metadata_requirements(metadata)
        assert is_valid is False
        assert any("Tissue field is empty" in r for r in reasons)

    def test_whitespace_tissue_field(self):
        """Test exclusion for whitespace-only tissue field"""
        metadata = {
            "tissue": "   ",
            "herbivore_type": "aphid",
            "replicates": 3
        }
        is_valid, reasons = verify_metadata_requirements(metadata)
        assert is_valid is False
        assert any("Tissue field is empty" in r for r in reasons)


class TestVerifyFastqMetadata:
    """Tests for the main verification function"""

    def test_verify_with_synthetic_mode(self):
        """Test verification in synthetic mode"""
        # Create a temporary manifest
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            manifest_data = {
                "entries": [
                    {"accession_id": "SRR123456", "checksum": "abc123"},
                    {"accession_id": "SRR789012", "checksum": "def456"}
                ]
            }
            json.dump(manifest_data, f)
            manifest_path = f.name

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                output_path = f.name

            try:
                report = verify_fastq_metadata(
                    manifest_path,
                    output_path,
                    mode="synthetic"
                )

                assert report["mode"] == "synthetic"
                assert report["total_studies"] == 2
                assert len(report["verified_studies"]) == 2
                assert len(report["excluded_studies"]) == 0

                # Check that output file was created
                assert os.path.exists(output_path)

                # Verify file content
                with open(output_path, 'r') as f:
                    saved_report = json.load(f)
                assert saved_report == report

            finally:
                os.unlink(output_path)

        finally:
            os.unlink(manifest_path)

    def test_verify_with_real_mode_no_network(self):
        """Test verification in real mode when network fails"""
        # Create a temporary manifest
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            manifest_data = {
                "entries": [
                    {"accession_id": "SRR123456", "checksum": "abc123"}
                ]
            }
            json.dump(manifest_data, f)
            manifest_path = f.name

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                output_path = f.name

            try:
                # Mock the fetch function to simulate failure
                with patch('src.data.verify_metadata.fetch_sra_metadata', return_value=None):
                    report = verify_fastq_metadata(
                        manifest_path,
                        output_path,
                        mode="real"
                    )

                    assert report["total_studies"] == 1
                    assert len(report["verified_studies"]) == 0
                    assert len(report["excluded_studies"]) == 1
                    assert report["excluded_studies"][0]["status"] == "excluded"
                    assert "Failed to fetch metadata" in report["excluded_studies"][0]["reason"]

            finally:
                os.unlink(output_path)

        finally:
            os.unlink(manifest_path)

    def test_verify_with_real_mode_success(self):
        """Test verification in real mode with successful metadata fetch"""
        # Create a temporary manifest
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            manifest_data = {
                "entries": [
                    {"accession_id": "SRR123456", "checksum": "abc123"}
                ]
            }
            json.dump(manifest_data, f)
            manifest_path = f.name

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                output_path = f.name

            try:
                # Mock successful metadata fetch
                mock_metadata = {
                    "tissue": "leaf",
                    "herbivore": "aphid",
                    "replicate": 3
                }

                with patch('src.data.verify_metadata.fetch_sra_metadata', return_value=mock_metadata):
                    report = verify_fastq_metadata(
                        manifest_path,
                        output_path,
                        mode="real"
                    )

                    assert report["total_studies"] == 1
                    assert len(report["verified_studies"]) == 1
                    assert len(report["excluded_studies"]) == 0
                    assert report["verified_studies"][0]["status"] == "verified"
                    assert report["verified_studies"][0]["metadata"]["tissue"] == "leaf"

            finally:
                os.unlink(output_path)

        finally:
            os.unlink(manifest_path)