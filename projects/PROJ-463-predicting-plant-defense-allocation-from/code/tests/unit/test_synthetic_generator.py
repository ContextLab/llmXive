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
import sys

# Add code directory to path if needed
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from src.data.synthetic_generator import (
    generate_synthetic_tpm_matrix,
    calculate_manifest_entry,
    generate_synthetic_tpm_study,
    save_synthetic_manifest
)
from src.utils.config import get_housekeeping_genes


class TestSyntheticGenerator:
    """Test suite for synthetic data generation."""

    def test_generate_synthetic_tpm_matrix_structure(self):
        """Test that generated TPM matrix has correct structure."""
        df = generate_synthetic_tpm_matrix(n_samples=10, n_genes=100, seed=42)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 100  # n_genes
        assert len(df.columns) == 10  # n_samples
        assert all(df > 0).all().all()  # All values positive

    def test_generate_synthetic_tpm_matrix_housekeeping_stability(self):
        """Test that housekeeping genes have stable expression."""
        df = generate_synthetic_tpm_matrix(n_samples=20, n_genes=1000, seed=42)
        
        hk_genes = get_housekeeping_genes()
        # Check if any housekeeping genes are in the matrix
        hk_in_matrix = [g for g in hk_genes if g in df.index]
        
        if len(hk_in_matrix) > 0:
            for gene in hk_in_matrix[:5]:  # Test first 5 found
                gene_data = df.loc[gene]
                cv = gene_data.std() / gene_data.mean()
                # Housekeeping genes should have low CV (< 0.2)
                assert cv < 0.2, f"Housekeeping gene {gene} has high CV: {cv}"

    def test_generate_synthetic_tpm_matrix_study_labels(self):
        """Test that study labels are correctly assigned."""
        df = generate_synthetic_tpm_matrix(n_samples=12, n_genes=100, n_studies=3, seed=42)
        
        assert 'study_labels' in df.attrs
        assert len(df.attrs['study_labels']) == len(df.columns)
        assert all(label in range(3) for label in df.attrs['study_labels'])

    def test_calculate_manifest_entry(self):
        """Test manifest entry calculation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("test,data\n1,2\n")
            temp_path = Path(f.name)
        
        try:
            entry = calculate_manifest_entry(temp_path, source_type="synthetic")
            
            assert 'file_name' in entry
            assert 'checksum' in entry
            assert entry['source_type'] == "synthetic"
            assert 'provenance' in entry
            assert 'generated_at' in entry['provenance']
            assert 'tool_versions' in entry['provenance']
            
            # Verify checksum is valid SHA256
            assert len(entry['checksum']) == 64  # SHA256 hex length
            
        finally:
            os.unlink(temp_path)

    def test_generate_synthetic_tpm_study_full_pipeline(self):
        """Test complete synthetic study generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "synthetic"
            output_dir.mkdir()
            
            result = generate_synthetic_tpm_study(
                output_dir=output_dir,
                n_samples=10,
                n_genes=500,
                n_studies=2,
                seed=42
            )
            
            # Check all files exist
            assert Path(result['tpm_file']).exists()
            assert Path(result['metadata_file']).exists()
            assert Path(result['manifest_file']).exists()
            
            # Verify TPM file content
            tpm_df = pd.read_csv(result['tpm_file'], index_col=0)
            assert len(tpm_df) == 500
            assert len(tpm_df.columns) == 10
            assert all(tpm_df > 0).all().all()
            
            # Verify metadata
            with open(result['metadata_file']) as f:
                metadata = json.load(f)
            assert metadata['n_samples'] == 10
            assert metadata['n_genes'] == 500
            assert metadata['n_studies'] == 2
            
            # Verify manifest
            with open(result['manifest_file']) as f:
                manifest = json.load(f)
            assert 'entries' in manifest
            assert len(manifest['entries']) == 2
            assert all('checksum' in entry for entry in manifest['entries'])
            assert all(entry['source_type'] == 'synthetic' for entry in manifest['entries'])

    def test_synthetic_data_not_in_raw(self):
        """Verify synthetic data is not written to data/raw/."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "synthetic"
            output_dir.mkdir()
            
            result = generate_synthetic_tpm_study(output_dir=output_dir)
            
            # Check that files are in synthetic directory, not raw
            assert "synthetic" in result['tpm_file']
            assert "raw" not in result['tpm_file']
            assert "synthetic" in result['manifest_file']
            assert "raw" not in result['manifest_file']

    def test_manifest_schema_compliance(self):
        """Test that manifest follows required schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "synthetic"
            output_dir.mkdir()
            
            result = generate_synthetic_tpm_study(output_dir=output_dir)
            
            with open(result['manifest_file']) as f:
                manifest = json.load(f)
            
            # Check top-level keys
            assert 'version' in manifest
            assert 'generated_at' in manifest
            assert 'entries' in manifest
            
            # Check entry schema
            for entry in manifest['entries']:
                assert 'file_name' in entry
                assert 'checksum' in entry
                assert 'source_type' in entry
                assert 'provenance' in entry
                
                # Check provenance schema
                prov = entry['provenance']
                assert 'generated_at' in prov
                assert 'tool_versions' in prov
                
                # Check tool versions
                tools = prov['tool_versions']
                assert 'python' in tools
                assert 'numpy' in tools
                assert 'pandas' in tools
        
        assert all(isinstance(v, (int, float, str, bool, type(None))) for v in metadata.values())

    def test_reproducibility_with_seed(self):
        """Test that same seed produces same results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir1 = Path(tmpdir) / "synthetic1"
            output_dir2 = Path(tmpdir) / "synthetic2"
            output_dir1.mkdir()
            output_dir2.mkdir()
            
            result1 = generate_synthetic_tpm_study(output_dir=output_dir1, seed=123)
            result2 = generate_synthetic_tpm_study(output_dir=output_dir2, seed=123)
            
            # Load TPM data
            df1 = pd.read_csv(result1['tpm_file'], index_col=0)
            df2 = pd.read_csv(result2['tpm_file'], index_col=0)
            
            # Should be identical
            assert df1.equals(df2)
            
            # Checksums should match
            assert result1['entries'][0]['checksum'] == result2['entries'][0]['checksum']

    def test_large_matrix_generation(self):
        """Test generation of larger matrices."""
        df = generate_synthetic_tpm_matrix(n_samples=50, n_genes=5000, seed=42)
        
        assert len(df) == 5000
        assert len(df.columns) == 50
        assert df.notna().all().all()
        assert (df > 0).all().all().all()

    def test_metadata_contains_study_labels(self):
        """Test that metadata includes study labels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "synthetic"
            output_dir.mkdir()
            
            result = generate_synthetic_tpm_study(output_dir=output_dir, n_studies=3)
            
            with open(result['metadata_file']) as f:
                metadata = json.load(f)
            
            assert 'study_labels' in metadata
            assert len(metadata['study_labels']) == metadata['n_samples']
            assert all(label in range(3) for label in metadata['study_labels'])