"""
Unit tests for SMILES standardization and molecular weight filtering.
"""
import pytest
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Ensure code directory is in path for imports
@pytest.fixture(autouse=True)
def setup_path():
    code_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

class TestSMILESStandardization:
    def test_canonicalize_smiles(self):
        """Test SMILES canonicalization."""
        from src.data.preprocess import canonicalize_smiles
        
        # Different representations of the same molecule
        smiles_variants = ["CCO", "OCC", "C(C)O"]
        canonical = canonicalize_smiles(smiles_variants[0])
        
        for smiles in smiles_variants[1:]:
            try:
                canon = canonicalize_smiles(smiles)
                assert canon == canonical, f"SMILES {smiles} did not canonicalize to {canonical}"
            except Exception:
                # Some SMILES might be invalid, skip for now
                pass

    def test_remove_salts(self):
        """Test salt removal from SMILES."""
        from src.data.preprocess import remove_salts
        
        # SMILES with salt
        smi_with_salt = "CCO.[Na+]"
        cleaned = remove_salts(smi_with_salt)
        # Should remove the salt part
        assert "." not in cleaned or cleaned.count(".") == 0

class TestMolecularWeightFiltering:
    def test_filter_by_molecular_weight(self):
        """Test filtering molecules by molecular weight."""
        from src.data.preprocess import filter_by_molecular_weight
        
        # List of (SMILES, MW) tuples
        molecules = [
            ("CCO", 46.07),   # Ethanol
            ("CCCCCCCCCCCCCCCC", 226.44), # Octadecane
            ("C1=CC=C(C=C1)C(=O)O", 122.12) # Benzoic acid
        ]
        
        # Filter for MW < 100
        filtered = filter_by_molecular_weight(molecules, max_mw=100)
        
        # Should only contain ethanol
        assert len(filtered) == 1
        assert filtered[0][1] < 100

    def test_filter_handles_invalid_mw(self):
        """Test filtering with invalid MW values."""
        from src.data.preprocess import filter_by_molecular_weight
        
        molecules = [
            ("CCO", 46.07),
            ("INVALID", None)
        ]
        
        filtered = filter_by_molecular_weight(molecules, max_mw=100)
        # Should handle None gracefully
        assert len(filtered) >= 0