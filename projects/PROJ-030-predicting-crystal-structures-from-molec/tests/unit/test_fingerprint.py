"""
Unit tests for fingerprint generation module.
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
import json
import pandas as pd

from code.ingestion.fingerprint import (
    smiles_to_mol,
    generate_ecfp4,
    get_molecular_weight,
    process_molecule_for_fingerprint,
    fingerprints_to_bit_vectors,
    generate_fingerprints_for_dataset
)
from code.ingestion.fingerprint import FingerprintError


class TestSmilesToMol:
    """Tests for smiles_to_mol function."""
    
    def test_valid_smiles(self):
        """Test conversion of valid SMILES."""
        smiles = "CCO"  # Ethanol
        mol = smiles_to_mol(smiles)
        assert mol is not None
        assert mol.GetNumAtoms() == 3
    
    def test_invalid_smiles(self):
        """Test handling of invalid SMILES."""
        smiles = "invalid_smiles_123"
        mol = smiles_to_mol(smiles)
        assert mol is None
    
    def test_empty_smiles(self):
        """Test handling of empty SMILES."""
        mol = smiles_to_mol("")
        assert mol is None
    
    def test_none_smiles(self):
        """Test handling of None SMILES."""
        mol = smiles_to_mol(None)
        assert mol is None
    
    def test_complex_molecule(self):
        """Test conversion of complex molecule."""
        smiles = "c1ccccc1"  # Benzene
        mol = smiles_to_mol(smiles)
        assert mol is not None
        assert mol.GetNumAtoms() == 6


class TestGenerateECFP4:
    """Tests for generate_ecfp4 function."""
    
    def test_basic_fingerprint(self):
        """Test basic fingerprint generation."""
        mol = smiles_to_mol("CCO")
        fp = generate_ecfp4(mol)
        assert isinstance(fp, np.ndarray)
        assert fp.shape == (2048,)
        assert set(fp).issubset({0, 1})
    
    def test_custom_radius(self):
        """Test fingerprint with custom radius."""
        mol = smiles_to_mol("CCO")
        fp = generate_ecfp4(mol, radius=3)
        assert fp.shape == (2048,)
    
    def test_custom_bits(self):
        """Test fingerprint with custom number of bits."""
        mol = smiles_to_mol("CCO")
        fp = generate_ecfp4(mol, n_bits=1024)
        assert fp.shape == (1024,)
    
    def test_fingerprint_error(self):
        """Test error handling in fingerprint generation."""
        # This should not raise an error for valid molecules
        mol = smiles_to_mol("CCO")
        with pytest.raises(FingerprintError):
            # Force an error by passing invalid mol
            generate_ecfp4(None)

class TestGetMolecularWeight:
    """Tests for get_molecular_weight function."""
    
    def test_molecular_weight(self):
        """Test molecular weight calculation."""
        mol = smiles_to_mol("CCO")  # Ethanol: C2H6O
        mw = get_molecular_weight(mol)
        assert mw is not None
        # Ethanol MW is approximately 46.07 g/mol
        assert 45 < mw < 47
    
    def test_invalid_mol(self):
        """Test handling of invalid molecule."""
        mw = get_molecular_weight(None)
        assert mw is None

class TestProcessMoleculeForFingerprint:
    """Tests for process_molecule_for_fingerprint function."""
    
    def test_successful_processing(self):
        """Test successful molecule processing."""
        fp, mw, status = process_molecule_for_fingerprint("CCO")
        assert status == 'success'
        assert fp is not None
        assert mw is not None
        assert fp.shape == (2048,)
    
    def test_parse_error(self):
        """Test handling of parse error."""
        fp, mw, status = process_molecule_for_fingerprint("invalid_smiles")
        assert status == 'parse_error'
        assert fp is None
    
    def test_mw_exclusion_high(self):
        """Test MW-based exclusion for high molecular weight."""
        # Large molecule
        smiles = "C" * 100  # Very long carbon chain
        fp, mw, status = process_molecule_for_fingerprint(smiles, max_mw=50.0)
        assert status == 'mw_excluded'
        assert fp is None
    
    def test_mw_exclusion_low(self):
        """Test MW-based exclusion for low molecular weight."""
        # Small molecule
        fp, mw, status = process_molecule_for_fingerprint("C", min_mw=20.0)
        assert status == 'mw_excluded'
        assert fp is None

class TestFingerprintsToBitVectors:
    """Tests for fingerprints_to_bit_vectors function."""
    
    def test_conversion(self):
        """Test conversion of fingerprints to bit vectors."""
        fps = [
            np.array([1, 0, 1, 0, 1]),
            np.array([0, 0, 1, 1, 0])
        ]
        bit_vectors = fingerprints_to_bit_vectors(fps)
        assert len(bit_vectors) == 2
        assert bit_vectors[0] == "1,0,1,0,1"
        assert bit_vectors[1] == "0,0,1,1,0"

class TestGenerateFingerprintsForDataset:
    """Tests for generate_fingerprints_for_dataset function."""
    
    def test_basic_generation(self):
        """Test basic fingerprint generation for dataset."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("smiles,space_group\n")
            f.write("CCO,P1\n")
            f.write("c1ccccc1,P21\n")
            f.write("CC(=O)O,P1\n")
            input_path = Path(f.name)
        
        # Create temporary output paths
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.csv"
            exclusion_log_path = Path(tmpdir) / "exclusion_log.json"
            
            stats = generate_fingerprints_for_dataset(
                input_file=input_path,
                output_file=output_path,
                exclusion_log_file=exclusion_log_path,
                chunk_size=2
            )
            
            # Verify results
            assert stats['total_rows'] == 3
            assert stats['success'] == 3
            assert stats['parse_errors'] == 0
            assert output_path.exists()
            assert exclusion_log_path.exists()
            
            # Verify output file content
            df = pd.read_csv(output_path)
            assert len(df) == 3
            assert 'fingerprint' in df.columns
            assert 'molecular_weight' in df.columns
            
            # Verify exclusion log
            with open(exclusion_log_path, 'r') as f:
                exclusion_data = json.load(f)
            assert 'excluded_rows' in exclusion_data
            assert 'summary' in exclusion_data
    
    def test_mw_filtering(self):
        """Test MW-based filtering during generation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("smiles,space_group\n")
            f.write("C,P1\n")  # Small molecule
            f.write("CCO,P1\n")  # Medium molecule
            f.write("C" * 50 + "O", "P1\n")  # Large molecule
            input_path = Path(f.name)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.csv"
            exclusion_log_path = Path(tmpdir) / "exclusion_log.json"
            
            stats = generate_fingerprints_for_dataset(
                input_file=input_path,
                output_file=output_path,
                exclusion_log_file=exclusion_log_path,
                max_mw=100.0
            )
            
            # Verify results
            assert stats['total_rows'] == 3
            assert stats['mw_excluded'] >= 1  # At least one large molecule excluded
            assert output_path.exists()
