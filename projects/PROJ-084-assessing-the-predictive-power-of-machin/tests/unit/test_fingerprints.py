"""
Unit tests for fingerprint generation.
Tests T013: Verify fingerprint dimensionality (ECFP4=2048, MACCS=167).
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json

from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys

# Import the functions to test
from preprocessing.fingerprints import (
    generate_ecfp4,
    generate_maccs,
    generate_fingerprints_batch,
    process_fingerprints_chunked,
    ECFP_LENGTH,
    MACCS_LENGTH
)

class TestFingerprintDimensions:
    """Test that fingerprints have correct dimensions."""

    def test_ecfp4_length(self):
        """Verify ECFP4 fingerprint length is 2048."""
        smiles = "CCO"  # Ethanol
        fp = generate_ecfp4(smiles)
        assert fp is not None, "ECFP4 generation failed"
        assert len(fp) == ECFP_LENGTH, f"ECFP4 length is {len(fp)}, expected {ECFP_LENGTH}"
        assert ECFP_LENGTH == 2048, "ECFP_LENGTH constant should be 2048"

    def test_maccs_length(self):
        """Verify MACCS fingerprint length is 167."""
        smiles = "CCO"  # Ethanol
        fp = generate_maccs(smiles)
        assert fp is not None, "MACCS generation failed"
        assert len(fp) == MACCS_LENGTH, f"MACCS length is {len(fp)}, expected {MACCS_LENGTH}"
        assert MACCS_LENGTH == 167, "MACCS_LENGTH constant should be 167"

    def test_ecfp4_with_complex_molecule(self):
        """Test ECFP4 with a more complex molecule."""
        smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
        fp = generate_ecfp4(smiles)
        assert fp is not None
        assert len(fp) == 2048

    def test_maccs_with_complex_molecule(self):
        """Test MACCS with a more complex molecule."""
        smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
        fp = generate_maccs(smiles)
        assert fp is not None
        assert len(fp) == 167

    def test_invalid_smiles_returns_none(self):
        """Test that invalid SMILES returns None."""
        assert generate_ecfp4("invalid_smiles") is None
        assert generate_maccs("invalid_smiles") is None

    def test_empty_smiles_returns_none(self):
        """Test that empty SMILES returns None."""
        assert generate_ecfp4("") is None
        assert generate_maccs("") is None

    def test_batch_generation_dimensions(self):
        """Test batch generation maintains correct dimensions."""
        df = pd.DataFrame({
            'smiles': ['CCO', 'CC(=O)Oc1ccccc1C(=O)O', 'invalid'],
            'yield': [50.0, 75.0, 60.0]
        })
        
        result = generate_fingerprints_batch(df)
        
        assert 'fingerprint_ecfp' in result.columns
        assert 'fingerprint_maccs' in result.columns
        
        # Check valid rows have correct dimensions
        assert len(result['fingerprint_ecfp'].iloc[0]) == 2048
        assert len(result['fingerprint_maccs'].iloc[0]) == 167
        assert len(result['fingerprint_ecfp'].iloc[1]) == 2048
        assert len(result['fingerprint_maccs'].iloc[1]) == 167

class TestFingerprintContent:
    """Test fingerprint content and properties."""

    def test_ecfp4_bit_values(self):
        """Verify ECFP4 contains only 0 and 1."""
        fp = generate_ecfp4("CCO")
        assert all(v in [0, 1] for v in fp), "ECFP4 should only contain 0 and 1"

    def test_maccs_bit_values(self):
        """Verify MACCS contains only 0 and 1."""
        fp = generate_maccs("CCO")
        assert all(v in [0, 1] for v in fp), "MACCS should only contain 0 and 1"

    def test_ecfp4_different_molecules_different_fingerprints(self):
        """Verify different molecules produce different fingerprints."""
        fp1 = generate_ecfp4("CCO")
        fp2 = generate_ecfp4("CCCO")
        assert not np.array_equal(fp1, fp2), "Different molecules should have different fingerprints"

    def test_maccs_different_molecules_different_fingerprints(self):
        """Verify different molecules produce different MACCS fingerprints."""
        fp1 = generate_maccs("CCO")
        fp2 = generate_maccs("CCCO")
        assert not np.array_equal(fp1, fp2), "Different molecules should have different MACCS fingerprints"

class TestChunkedProcessing:
    """Test chunked processing functionality."""

    def test_chunked_processing_creates_output(self):
        """Verify chunked processing creates output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"
            
            # Create test data
            df = pd.DataFrame({
                'smiles': ['CCO', 'CCCO', 'CCCCO'] * 100,
                'yield': [50.0] * 300
            })
            df.to_parquet(input_path)
            
            # Process
            result = process_fingerprints_chunked(str(input_path), str(output_path))
            
            # Verify output exists
            assert output_path.exists(), "Output file should be created"
            assert len(result) == 300, "All rows should be processed"
            
            # Verify dimensions
            assert len(result['fingerprint_ecfp'].iloc[0]) == 2048
            assert len(result['fingerprint_maccs'].iloc[0]) == 167

    def test_chunked_processing_logs_dimensions(self):
        """Verify chunked processing creates dimension log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"
            log_path = Path(tmpdir) / "fingerprint_dimensions.log"
            
            # Create test data
            df = pd.DataFrame({
                'smiles': ['CCO'] * 10,
                'yield': [50.0] * 10
            })
            df.to_parquet(input_path)
            
            # Temporarily override DATA_RESULTS_DIR
            import preprocessing.fingerprints as fp_module
            original_dir = fp_module.DATA_RESULTS_DIR
            fp_module.DATA_RESULTS_DIR = Path(tmpdir)
            
            try:
                process_fingerprints_chunked(str(input_path), str(output_path))
                
                # Check log file exists
                assert log_path.exists(), "Dimension log should be created"
                
                # Check log content
                with open(log_path, 'r') as f:
                    content = f.read()
                
                assert "2048" in content, "Log should mention ECFP4 length"
                assert "167" in content, "Log should mention MACCS length"
            finally:
                fp_module.DATA_RESULTS_DIR = original_dir