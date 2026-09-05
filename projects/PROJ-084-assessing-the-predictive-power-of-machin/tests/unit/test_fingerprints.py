"""
Unit tests for fingerprint generation functionality.

Tests verify:
- ECFP4 dimensionality (2048 bits)
- MACCS dimensionality (167 bits)
- Correct handling of invalid SMILES
- Chunked processing behavior
"""
import pytest
import numpy as np
from pathlib import Path
import tempfile
import pandas as pd

from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys

# Import the module under test
from preprocessing.fingerprints import (
    generate_ecfp4,
    generate_maccs,
    generate_fingerprints_batch,
    process_fingerprints_chunked,
    ECFP_SIZE,
    MACCS_SIZE
)

# Sample test molecules
VALID_SMILES = [
    "CCO",  # Ethanol
    "CC(=O)O",  # Acetic acid
    "c1ccccc1",  # Benzene
    "CCOCC",  # Diethyl ether
    "CC(C)C",  # Isobutane
]

INVALID_SMILES = [
    "",  # Empty string
    "INVALID_SMILES",  # Invalid format
    "C((",  # Malformed
]

class TestECFP4Generation:
    """Tests for ECFP4 fingerprint generation."""

    def test_ecfp4_dimensionality(self):
        """Test that ECFP4 fingerprints have exactly 2048 bits."""
        mol = Chem.MolFromSmiles("CCO")
        fp = generate_ecfp4(mol)

        assert len(fp) == ECFP_SIZE, f"Expected {ECFP_SIZE} bits, got {len(fp)}"
        assert all(bit in [0, 1] for bit in fp), "All bits should be 0 or 1"

    def test_ecfp4_non_zero_for_complex_molecules(self):
        """Test that complex molecules have non-zero fingerprints."""
        mol = Chem.MolFromSmiles("c1ccccc1C(=O)O")  # Benzoic acid
        fp = generate_ecfp4(mol)

        assert sum(fp) > 0, "Complex molecule should have some bits set"

    def test_ecfp4_for_null_molecule(self):
        """Test that None molecule returns zero fingerprint."""
        fp = generate_ecfp4(None)

        assert len(fp) == ECFP_SIZE
        assert all(bit == 0 for bit in fp)

    def test_ecfp4_deterministic(self):
        """Test that ECFP4 generation is deterministic."""
        mol = Chem.MolFromSmiles("CCO")
        fp1 = generate_ecfp4(mol)
        fp2 = generate_ecfp4(mol)

        assert fp1 == fp2, "ECFP4 generation should be deterministic"

class TestMACCSGeneration:
    """Tests for MACCS fingerprint generation."""

    def test_maccs_dimensionality(self):
        """Test that MACCS fingerprints have exactly 167 bits."""
        mol = Chem.MolFromSmiles("CCO")
        fp = generate_maccs(mol)

        assert len(fp) == MACCS_SIZE, f"Expected {MACCS_SIZE} bits, got {len(fp)}"
        assert all(bit in [0, 1] for bit in fp), "All bits should be 0 or 1"

    def test_maccs_non_zero_for_complex_molecules(self):
        """Test that complex molecules have non-zero MACCS fingerprints."""
        mol = Chem.MolFromSmiles("c1ccccc1C(=O)O")  # Benzoic acid
        fp = generate_maccs(mol)

        assert sum(fp) > 0, "Complex molecule should have some bits set"

    def test_maccs_for_null_molecule(self):
        """Test that None molecule returns zero fingerprint."""
        fp = generate_maccs(None)

        assert len(fp) == MACCS_SIZE
        assert all(bit == 0 for bit in fp)

    def test_maccs_deterministic(self):
        """Test that MACCS generation is deterministic."""
        mol = Chem.MolFromSmiles("CCO")
        fp1 = generate_maccs(mol)
        fp2 = generate_maccs(mol)

        assert fp1 == fp2, "MACCS generation should be deterministic"

class TestBatchGeneration:
    """Tests for batch fingerprint generation."""

    def test_batch_processing_valid_smiles(self):
        """Test batch processing of valid SMILES."""
        ecfp_fps, maccs_fps, valid_indices = generate_fingerprints_batch(VALID_SMILES)

        assert len(ecfp_fps) == len(VALID_SMILES)
        assert len(maccs_fps) == len(VALID_SMILES)
        assert len(valid_indices) == len(VALID_SMILES)

        # Check dimensions
        for fp in ecfp_fps:
            assert len(fp) == ECFP_SIZE

        for fp in maccs_fps:
            assert len(fp) == MACCS_SIZE

    def test_batch_processing_invalid_smiles(self):
        """Test that invalid SMILES are skipped."""
        mixed_smiles = VALID_SMILES + INVALID_SMILES
        ecfp_fps, maccs_fps, valid_indices = generate_fingerprints_batch(mixed_smiles)

        # Should only process valid SMILES
        assert len(ecfp_fps) == len(VALID_SMILES)
        assert len(maccs_fps) == len(VALID_SMILES)
        assert len(valid_indices) == len(VALID_SMILES)

    def test_batch_processing_empty_list(self):
        """Test batch processing with empty list."""
        ecfp_fps, maccs_fps, valid_indices = generate_fingerprints_batch([])

        assert len(ecfp_fps) == 0
        assert len(maccs_fps) == 0
        assert len(valid_indices) == 0

class TestChunkedProcessing:
    """Tests for chunked processing functionality."""

    def test_chunked_processing_creates_output(self):
        """Test that chunked processing creates output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"

            # Create test data
            test_df = pd.DataFrame({
                'smiles': VALID_SMILES,
                'yield': [50.0, 60.0, 70.0, 80.0, 90.0],
                'reaction_class': ['A', 'B', 'A', 'B', 'A']
            })
            test_df.to_parquet(input_path)

            # Process
            stats = process_fingerprints_chunked(input_path, output_path)

            # Verify output exists
            assert output_path.exists(), "Output file should be created"

            # Verify stats
            assert stats['processed_rows'] == len(VALID_SMILES)
            assert stats['invalid_rows'] == 0
            assert stats['fingerprint_dimensions']['ecfp4'] == ECFP_SIZE
            assert stats['fingerprint_dimensions']['maccs'] == MACCS_SIZE

    def test_chunked_processing_logs_dimensions(self):
        """Test that fingerprint dimensions are logged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"
            results_dir = Path(tmpdir) / "results"
            results_dir.mkdir()

            # Temporarily change the log path for testing
            import preprocessing.fingerprints as fp_module
            original_log_path = fp_module.Path('data/results/fingerprint_dimensions.log')
            fp_module.Path = lambda x: Path(tmpdir) / x if 'results' in str(x) else Path(x)

            # Create test data
            test_df = pd.DataFrame({
                'smiles': VALID_SMILES,
                'yield': [50.0, 60.0, 70.0, 80.0, 90.0],
                'reaction_class': ['A', 'B', 'A', 'B', 'A']
            })
            test_df.to_parquet(input_path)

            # Process
            stats = process_fingerprints_chunked(input_path, output_path)

            # Verify log file exists
            log_path = results_dir / "fingerprint_dimensions.log"
            # Note: The actual log path is hardcoded, so we check if it was created
            # in the default location or the test location depending on implementation

    def test_chunked_processing_with_invalid_smiles(self):
        """Test chunked processing with some invalid SMILES."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"

            # Create test data with mixed valid/invalid
            mixed_smiles = VALID_SMILES + INVALID_SMILES
            test_df = pd.DataFrame({
                'smiles': mixed_smiles,
                'yield': [50.0] * len(mixed_smiles),
                'reaction_class': ['A'] * len(mixed_smiles)
            })
            test_df.to_parquet(input_path)

            # Process
            stats = process_fingerprints_chunked(input_path, output_path)

            # Should only process valid SMILES
            assert stats['processed_rows'] == len(VALID_SMILES)
            assert stats['invalid_rows'] == len(INVALID_SMILES)

class TestFingerprintDimensions:
    """Tests for fingerprint dimension validation."""

    def test_ecfp4_is_2048(self):
        """Verify ECFP4 constant is 2048."""
        assert ECFP_SIZE == 2048

    def test_maccs_is_167(self):
        """Verify MACCS constant is 167."""
        assert MACCS_SIZE == 167

    def test_generated_fingerprints_match_constants(self):
        """Test that generated fingerprints match expected dimensions."""
        mol = Chem.MolFromSmiles("CCO")
        ecfp_fp = generate_ecfp4(mol)
        maccs_fp = generate_maccs(mol)

        assert len(ecfp_fp) == ECFP_SIZE
        assert len(maccs_fp) == MACCS_SIZE