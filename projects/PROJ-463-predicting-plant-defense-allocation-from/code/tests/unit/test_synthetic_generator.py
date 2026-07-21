import pytest
import os
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.synthetic_generator import (
    generate_synthetic_counts,
    calculate_tpm_from_counts,
    _calculate_sha256
)
from src.utils.schemas import ManifestEntry

class TestSyntheticGenerator:
    """Tests for synthetic data generation functionality."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_generate_synthetic_counts_creates_files(self, temp_output_dir):
        """Test that synthetic counts generation creates expected files."""
        data_dict, manifest_path = generate_synthetic_counts(
            n_genes=100,
            n_samples=20,
            n_studies=2,
            output_dir=temp_output_dir,
            seed=42
        )
        
        # Check that data dictionary is populated
        assert len(data_dict) == 2
        assert all(isinstance(df, pd.DataFrame) for df in data_dict.values())
        
        # Check that manifest file exists
        assert os.path.exists(manifest_path)
        
        # Check manifest structure
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert "entries" in manifest
        assert len(manifest["entries"]) == 2
        
        # Check each entry has required fields
        for entry in manifest["entries"]:
            assert "file_name" in entry
            assert "checksum" in entry
            assert "source_type" in entry
            assert "provenance" in entry
            assert entry["source_type"] == "synthetic"
            assert "generated_at" in entry["provenance"]
            assert "tool_versions" in entry["provenance"]

    def test_synthetic_data_structure(self, temp_output_dir):
        """Test that generated data has correct structure."""
        n_genes = 50
        n_samples = 10
        
        data_dict, _ = generate_synthetic_counts(
            n_genes=n_genes,
            n_samples=n_samples,
            n_studies=1,
            output_dir=temp_output_dir,
            seed=42
        )
        
        df = list(data_dict.values())[0]
        
        # Check dimensions
        assert df.shape[0] == n_samples
        assert df.shape[1] == n_genes + 2  # +2 for tissue and condition columns
        
        # Check that all gene columns are numeric
        gene_cols = [col for col in df.columns if col.startswith("GENE_")]
        assert len(gene_cols) == n_genes
        
        # Check for non-negative values
        assert (df[gene_cols] >= 0).all().all()

    def test_tpm_conversion(self):
        """Test TPM calculation from counts."""
        # Create dummy counts
        np.random.seed(42)
        counts = pd.DataFrame(
            np.random.randint(1, 100, size=(5, 10)),
            columns=[f"GENE_{i:03d}" for i in range(10)]
        )
        
        gene_lengths = {f"GENE_{i:03d}": np.random.uniform(1000, 3000) for i in range(10)}
        
        tpm = calculate_tpm_from_counts(counts, gene_lengths)
        
        # Check dimensions
        assert tpm.shape == counts.shape
        
        # Check that TPM values are positive
        assert (tpm > 0).all().all()
        
        # Check that scaling is approximately correct (sum of TPM per sample ~ 1e6)
        for sample in tpm.index:
            sample_sum = tpm.loc[sample].sum()
            assert 0.9e6 < sample_sum < 1.1e6

    def test_checksum_consistency(self, temp_output_dir):
        """Test that checksums are consistent and reproducible."""
        # Generate data twice with same seed
        _, manifest1 = generate_synthetic_counts(
            n_genes=50,
            n_samples=10,
            n_studies=1,
            output_dir=temp_output_dir,
            seed=42
        )
        
        # Read first manifest
        with open(manifest1, 'r') as f:
            manifest_data1 = json.load(f)
        checksum1 = manifest_data1["entries"][0]["checksum"]
        
        # Generate again with same seed (overwrites files)
        _, manifest2 = generate_synthetic_counts(
            n_genes=50,
            n_samples=10,
            n_studies=1,
            output_dir=temp_output_dir,
            seed=42
        )
        
        with open(manifest2, 'r') as f:
            manifest_data2 = json.load(f)
        checksum2 = manifest_data2["entries"][0]["checksum"]
        
        # Checksums should be identical
        assert checksum1 == checksum2

    def test_manifest_schema_compliance(self, temp_output_dir):
        """Test that manifest entries comply with schema."""
        _, manifest_path = generate_synthetic_counts(
            n_genes=50,
            n_samples=10,
            n_studies=1,
            output_dir=temp_output_dir,
            seed=42
        )
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Validate structure
        assert isinstance(manifest["entries"], list)
        
        for entry in manifest["entries"]:
            # Validate required fields
            assert isinstance(entry["file_name"], str)
            assert isinstance(entry["checksum"], str)
            assert len(entry["checksum"]) == 64  # SHA256 hex
            assert entry["source_type"] == "synthetic"
            assert isinstance(entry["provenance"], dict)
            assert "generated_at" in entry["provenance"]
            assert isinstance(entry["provenance"]["generated_at"], str)
            assert "tool_versions" in entry["provenance"]

    def test_no_write_to_raw(self, temp_output_dir):
        """Ensure synthetic data is not written to data/raw directory."""
        # Create a fake 'raw' directory structure
        raw_dir = Path(temp_output_dir) / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate synthetic data
        _, manifest_path = generate_synthetic_counts(
            n_genes=50,
            n_samples=10,
            n_studies=1,
            output_dir=temp_output_dir,
            seed=42
        )
        
        # Check that no files were written to raw directory
        raw_files = list(raw_dir.glob("*"))
        assert len(raw_files) == 0, "Synthetic data should not be written to data/raw"

    def test_housekeeping_genes_included(self, temp_output_dir):
        """Test that housekeeping genes are included in generated data."""
        from src.utils.config import get_housekeeping_genes
        
        hk_genes = get_housekeeping_genes()
        
        _, manifest_path = generate_synthetic_counts(
            n_genes=100,
            n_samples=10,
            n_studies=1,
            output_dir=temp_output_dir,
            seed=42
        )
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Read the generated CSV to check gene names
        csv_path = Path(temp_output_dir) / manifest["entries"][0]["file_name"]
        df = pd.read_csv(csv_path, index_col=0)
        
        # Check that at least some housekeeping genes are present
        gene_cols = [col for col in df.columns if col.startswith("GENE_")]
        hk_in_data = [g for g in hk_genes if g in gene_cols]
        
        assert len(hk_in_data) > 0, "Some housekeeping genes should be present"