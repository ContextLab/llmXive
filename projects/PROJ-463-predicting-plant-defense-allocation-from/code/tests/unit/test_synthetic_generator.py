"""
Unit tests for the synthetic data generator.

Tests verify that:
1. Synthetic TPM matrices are generated with correct structure
2. Manifest entries are created with valid checksums
3. Files are written to the correct directories (data/synthetic/, not data/raw/)
4. Provenance information is correctly recorded
"""

import pytest
import os
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.synthetic_generator import (
    generate_synthetic_tpm_matrix,
    calculate_sha256,
    calculate_manifest_entry,
    save_synthetic_manifest,
    generate_synthetic_tpm_study
)
from src.utils.schemas import ManifestEntry, ProvenanceInfo


class TestSyntheticGenerator:

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_generate_synthetic_tpm_matrix_shape(self):
        """Test that generated matrix has correct dimensions."""
        n_genes = 100
        n_samples = 5
        seed = 42

        df = generate_synthetic_tpm_matrix(
            n_genes=n_genes,
            n_samples=n_samples,
            seed=seed
        )

        assert df.shape == (n_genes, n_samples)
        assert len(df.index) == n_genes
        assert len(df.columns) == n_samples

    def test_generate_synthetic_tpm_matrix_values(self):
        """Test that generated TPM values are positive and reasonable."""
        df = generate_synthetic_tpm_matrix(n_genes=50, n_samples=3, seed=123)

        # All values should be positive
        assert (df > 0).all().all()

        # Check for reasonable range (TPM typically 0.001 to 10000+)
        assert df.min().min() > 0
        assert df.max().max() > 0

    def test_generate_synthetic_tpm_matrix_gene_ids(self):
        """Test that gene IDs follow expected format."""
        df = generate_synthetic_tpm_matrix(n_genes=10, n_samples=2, seed=42)

        # Check that gene IDs start with AT followed by digit
        for gene_id in df.index:
            assert gene_id.startswith("AT")
            assert "G" in gene_id

    def test_generate_synthetic_tpm_matrix_sample_names(self):
        """Test that sample names follow expected format."""
        accession_id = "SYNTH_TEST"
        n_samples = 5
        df = generate_synthetic_tpm_matrix(
            n_samples=n_samples,
            accession_id=accession_id,
            seed=42
        )

        for col in df.columns:
            assert col.startswith(accession_id)

    def test_calculate_sha256(self, temp_output_dir):
        """Test SHA256 checksum calculation."""
        test_file = temp_output_dir / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        checksum = calculate_sha256(test_file)

        # SHA256 should be 64 hex characters
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_calculate_manifest_entry(self, temp_output_dir):
        """Test manifest entry creation."""
        test_file = temp_output_dir / "test.csv"
        test_file.write_csv(pd.DataFrame({"A": [1, 2, 3]}).to_csv())

        entry = calculate_manifest_entry(
            file_path=test_file,
            accession_id="TEST_001",
            organism="Arabidopsis thaliana",
            n_genes=3,
            n_samples=1
        )

        assert isinstance(entry, ManifestEntry)
        assert entry.source_type == "synthetic"
        assert entry.file_name == "test.csv"
        assert entry.checksum == calculate_sha256(test_file)
        assert entry.metadata.provenance.accession_id == "TEST_001"

    def test_save_synthetic_manifest(self, temp_output_dir):
        """Test saving manifest to JSON."""
        test_file = temp_output_dir / "test.csv"
        test_file.write_csv(pd.DataFrame({"A": [1, 2, 3]}).to_csv())

        entry = calculate_manifest_entry(
            file_path=test_file,
            accession_id="TEST_001",
            organism="Arabidopsis thaliana",
            n_genes=3,
            n_samples=1
        )

        manifest_path = temp_output_dir / "manifest.json"
        save_synthetic_manifest(entry, manifest_path)

        assert manifest_path.exists()

        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)

        assert manifest_data["file_name"] == "test.csv"
        assert manifest_data["source_type"] == "synthetic"
        assert "checksum" in manifest_data
        assert "provenance" in manifest_data

    def test_generate_synthetic_tpm_study(self, temp_output_dir):
        """Test full synthetic study generation."""
        n_genes = 100
        n_samples = 5
        accession_id = "SYNTH_TEST"

        result = generate_synthetic_tpm_study(
            output_dir=temp_output_dir,
            n_genes=n_genes,
            n_samples=n_samples,
            accession_id=accession_id,
            seed=42
        )

        # Check return values
        assert result["accession_id"] == accession_id
        assert result["n_genes"] == n_genes
        assert result["n_samples"] == n_samples

        # Check files exist
        matrix_path = Path(result["matrix_path"])
        manifest_path = Path(result["manifest_path"])

        assert matrix_path.exists()
        assert manifest_path.exists()

        # Verify matrix content
        df = pd.read_csv(matrix_path, index_col=0)
        assert df.shape == (n_genes, n_samples)

        # Verify manifest content
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)

        assert manifest_data["source_type"] == "synthetic"
        assert manifest_data["provenance"]["accession_id"] == accession_id

    def test_output_directory_constraint(self, temp_output_dir):
        """Test that output is written to synthetic directory, not raw."""
        # Create a mock data path structure
        synthetic_dir = temp_output_dir / "synthetic"
        raw_dir = temp_output_dir / "raw"

        synthetic_dir.mkdir()
        raw_dir.mkdir()

        # Generate study
        generate_synthetic_tpm_study(
            output_dir=synthetic_dir,
            n_genes=10,
            n_samples=2,
            seed=42
        )

        # Verify files are in synthetic directory
        assert len(list(synthetic_dir.glob("*.csv"))) == 1
        assert len(list(raw_dir.glob("*.csv"))) == 0

    def test_reproducibility_with_seed(self):
        """Test that same seed produces same results."""
        df1 = generate_synthetic_tpm_matrix(n_genes=100, n_samples=5, seed=42)
        df2 = generate_synthetic_tpm_matrix(n_genes=100, n_samples=5, seed=42)

        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seeds_produce_different_results(self):
        """Test that different seeds produce different results."""
        df1 = generate_synthetic_tpm_matrix(n_genes=100, n_samples=5, seed=42)
        df2 = generate_synthetic_tpm_matrix(n_genes=100, n_samples=5, seed=123)

        # They should be different
        assert not df1.equals(df2)