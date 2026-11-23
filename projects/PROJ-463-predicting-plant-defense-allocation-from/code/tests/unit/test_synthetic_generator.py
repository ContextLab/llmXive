"""
Unit tests for synthetic data generator.
"""
import pytest
import os
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.synthetic_generator import (
    calculate_sha256,
    generate_synthetic_tpm_matrix,
    generate_synthetic_metadata,
    calculate_manifest_entry,
    save_synthetic_manifest,
    generate_synthetic_metadata_report,
    main
)
from src.utils.config import get_seed


class TestSyntheticGenerator:
    """Test cases for synthetic data generation functions."""

    def test_calculate_sha256(self):
        """Test SHA256 hash calculation."""
        test_string = "test_data"
        hash_result = calculate_sha256(test_string)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA256 produces 64 character hex string

    def test_generate_synthetic_tpm_matrix_shape(self):
        """Test that TPM matrix has correct dimensions."""
        num_samples = 10
        num_genes = 100
        seed = 42

        matrix = generate_synthetic_tpm_matrix(num_samples, num_genes, seed)

        assert matrix.shape == (num_genes, num_samples)
        assert len(matrix.index) == num_genes
        assert len(matrix.columns) == num_samples

    def test_generate_synthetic_tpm_matrix_distribution(self):
        """Test that TPM values follow expected log-normal distribution."""
        seed = 42
        matrix = generate_synthetic_tpm_matrix(100, 1000, seed)

        # Check that values are non-negative
        assert (matrix >= 0).all().all()

        # Check that there are some zeros (dropouts)
        zero_rate = (matrix == 0).sum().sum() / matrix.size
        assert 0 < zero_rate < 0.5  # Should have some zeros but not all

        # Check that values are in reasonable TPM range
        assert matrix.min().min() >= 0
        assert matrix.max().max() < 1e6  # TPM values should be reasonable

    def test_generate_synthetic_tpm_matrix_reproducibility(self):
        """Test that same seed produces same results."""
        seed = 42
        matrix1 = generate_synthetic_tpm_matrix(10, 20, seed)
        matrix2 = generate_synthetic_tpm_matrix(10, 20, seed)

        pd.testing.assert_frame_equal(matrix1, matrix2)

    def test_generate_synthetic_metadata_structure(self):
        """Test that metadata has correct structure."""
        num_species = 2
        num_tissues = 2
        num_treatments = 2
        seed = 42

        metadata = generate_synthetic_metadata(num_species, num_tissues, num_treatments, seed)

        assert isinstance(metadata, list)
        assert len(metadata) == 20  # NUM_SAMPLES default

        # Check each metadata entry has required fields
        required_fields = ["sample_id", "accession_id", "species", "tissue", "treatment", "replicates"]
        for entry in metadata:
            for field in required_fields:
                assert field in entry

    def test_generate_synthetic_metadata_values(self):
        """Test that metadata values are valid."""
        metadata = generate_synthetic_metadata(seed=42)

        for entry in metadata:
            assert entry["accession_id"] == "SYNTH_001"
            assert entry["species"] in ["Arabidopsis thaliana", "Solanum lycopersicum", "Zea mays"]
            assert entry["tissue"] in ["leaf", "root", "stem", "flower"]
            assert entry["treatment"] in ["control", "herbivore_attack"]
            assert entry["replicates"] >= 2

    def test_calculate_manifest_entry(self):
        """Test manifest entry calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "test.csv"
            df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
            metadata = [{"sample": "test"}]

            manifest = calculate_manifest_entry(tmp_path, df, metadata)

            assert "file_name" in manifest
            assert "checksum" in manifest
            assert "source_type" in manifest
            assert manifest["source_type"] == "synthetic"
            assert "provenance" in manifest
            assert "statistics" in manifest

    def test_save_synthetic_manifest(self):
        """Test saving synthetic manifest to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            manifest = {"test": "data", "number": 123}
            output_file = tmp_path / "manifest.json"

            save_synthetic_manifest(manifest, output_file)

            assert output_file.exists()
            with open(output_file, 'r') as f:
                loaded = json.load(f)
            assert loaded == manifest

    def test_generate_synthetic_metadata_report(self):
        """Test generating synthetic metadata verification report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            metadata = [{"sample_id": "test"}]
            report_file = tmp_path / "report.json"

            generate_synthetic_metadata_report(metadata, report_file)

            assert report_file.exists()
            with open(report_file, 'r') as f:
                report = json.load(f)

            assert report["mode"] == "synthetic"
            assert report["real_data_available"] is False
            assert "studies" in report
            assert "validation_summary" in report

    @patch('src.data.synthetic_generator.get_data_path')
    @patch('src.data.synthetic_generator.Path')
    def test_main_success(self, mock_path, mock_get_data_path):
        """Test main function success path."""
        mock_get_data_path.return_value = "/tmp/test"
        mock_path.return_value.mkdir = MagicMock()
        mock_path.return_value.__truediv__ = MagicMock(return_value=MagicMock())
        mock_path.return_value.__truediv__.return_value.mkdir = MagicMock()

        result = main()

        assert result == 0

    @patch('src.data.synthetic_generator.get_data_path')
    @patch('src.data.synthetic_generator.Path')
    @patch('src.data.synthetic_generator.generate_synthetic_tpm_matrix')
    def test_main_with_exception(self, mock_gen, mock_path, mock_get_data_path):
        """Test main function with exception."""
        mock_get_data_path.return_value = "/tmp/test"
        mock_path.return_value.mkdir = MagicMock()
        mock_path.return_value.__truediv__ = MagicMock(return_value=MagicMock())
        mock_path.return_value.__truediv__.return_value.mkdir = MagicMock()
        mock_gen.side_effect = Exception("Test error")

        result = main()

        assert result == 1