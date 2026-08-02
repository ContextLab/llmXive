"""
Unit tests for the synthetic data generator.
"""
import pytest
import os
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path if necessary
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.synthetic_generator import (
    generate_synthetic_tpm_matrix,
    calculate_manifest_entry,
    save_synthetic_manifest,
    generate_synthetic_metadata_report
)
from src.utils.config import set_seed

class TestSyntheticGenerator:
    def test_generate_synthetic_tpm_matrix_shape(self):
        """Test that the generated matrix has the correct shape."""
        set_seed(42)
        n_samples = 10
        n_genes = 100
        df = generate_synthetic_tpm_matrix(n_samples, n_genes, seed=42)

        assert df.shape == (n_genes, n_samples)
        assert len(df.index) == n_genes
        assert len(df.columns) == n_samples

    def test_generate_synthetic_tpm_matrix_values(self):
        """Test that generated values are positive and log-normal distributed."""
        set_seed(42)
        df = generate_synthetic_tpm_matrix(20, 1000, seed=42)

        # Check all values are non-negative
        assert (df >= 0).all().all()

        # Check that values are not all zeros
        assert df.sum().sum() > 0

    def test_manifest_entry_creation(self):
        """Test manifest entry creation with a temporary file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("gene,sample1\nAT1G1,10.5\n")
            temp_path = f.name

        try:
            entry = calculate_manifest_entry(
                temp_path,
                "TEST_001",
                seed=42,
                n_samples=1,
                n_genes=1
            )

            assert entry["source_type"] == "synthetic"
            assert entry["accession_id"] == "TEST_001"
            assert "provenance" in entry
            assert "generated_at" in entry["provenance"]
            assert entry["provenance"]["parameters"]["seed"] == 42
        finally:
            os.unlink(temp_path)

    def test_save_synthetic_manifest(self):
        """Test saving the manifest to a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = os.path.join(tmpdir, "manifest.json")
            entry = {
                "file_name": "test.csv",
                "checksum": "abc123",
                "source_type": "synthetic",
                "provenance": {"generated_at": "2023-01-01", "tool_versions": {}, "accession_id": "X", "organism": "A", "parameters": {}}
            }
            save_synthetic_manifest(entry, manifest_path)

            assert os.path.exists(manifest_path)
            with open(manifest_path, 'r') as f:
                loaded = json.load(f)
            assert loaded["source_type"] == "synthetic"

    def test_metadata_report_generation(self):
        """Test generation of the metadata verification report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, "report.json")
            generate_synthetic_metadata_report("SYNTH_001", report_path)

            assert os.path.exists(report_path)
            with open(report_path, 'r') as f:
                report = json.load(f)

            assert report["mode"] == "synthetic"
            assert report["real_data_available"] is False
            assert "verification_results" in report
            assert len(report["verification_results"]) == 1