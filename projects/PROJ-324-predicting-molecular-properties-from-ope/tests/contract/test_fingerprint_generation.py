"""
Contract test for fingerprint generation module.

This test verifies that the fingerprint generation module:
1. Correctly invokes obabel for valid SMILES.
2. Handles invalid SMILES gracefully.
3. Produces the expected output format.
"""

import pytest
import subprocess
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.fingerprints import (
    check_obabel_available,
    smiles_to_obabel_fingerprint,
    generate_fingerprints,
    FINGERPRINT_TYPES,
    PRIORITY_ORDER
)

class TestFingerprintGeneration:
    
    def test_obabel_available(self):
        """Test that obabel is available in the system."""
        # This might fail in environments without obabel, but we expect it to be there for the task
        # If not available, the test should indicate it, not crash
        available = check_obabel_available()
        # We don't assert True here because the environment might not have obabel installed
        # Instead, we skip if not available
        if not available:
            pytest.skip("Open Babel (obabel) is not available in PATH.")
        assert available, "Open Babel should be available."

    @pytest.mark.skipif(not check_obabel_available(), reason="Open Babel not available")
    def test_ecfp4_generation(self):
        """Test ECFP4 fingerprint generation for a known molecule."""
        smiles = "CCO"  # Ethanol
        fp = smiles_to_obabel_fingerprint(smiles, "ECFP4", timeout=10)
        
        assert fp is not None, "ECFP4 fingerprint should be generated."
        assert isinstance(fp, list), "Fingerprint should be a list."
        assert all(bit in [0, 1] for bit in fp), "Fingerprint bits should be 0 or 1."
        # ECFP4 typically has 1024 or 2048 bits. Let's check length is reasonable.
        assert len(fp) > 0, "Fingerprint should have at least one bit."

    @pytest.mark.skipif(not check_obabel_available(), reason="Open Babel not available")
    def test_maccs_generation(self):
        """Test MACCS fingerprint generation."""
        smiles = "CCO"  # Ethanol
        fp = smiles_to_obabel_fingerprint(smiles, "MACCS", timeout=10)
        
        assert fp is not None, "MACCS fingerprint should be generated."
        assert isinstance(fp, list), "Fingerprint should be a list."
        assert all(bit in [0, 1] for bit in fp), "Fingerprint bits should be 0 or 1."
        # MACCS keys are typically 166 bits.
        # We don't assert exact length as obabel might output differently, but it should be non-empty.
        assert len(fp) > 0, "Fingerprint should have at least one bit."

    @pytest.mark.skipif(not check_obabel_available(), reason="Open Babel not available")
    def test_fp2_generation(self):
        """Test FP2 fingerprint generation."""
        smiles = "CCO"  # Ethanol
        fp = smiles_to_obabel_fingerprint(smiles, "FP2", timeout=10)
        
        assert fp is not None, "FP2 fingerprint should be generated."
        assert isinstance(fp, list), "Fingerprint should be a list."
        assert all(bit in [0, 1] for bit in fp), "Fingerprint bits should be 0 or 1."
        assert len(fp) > 0, "Fingerprint should have at least one bit."

    @pytest.mark.skipif(not check_obabel_available(), reason="Open Babel not available")
    def test_invalid_smiles(self):
        """Test handling of invalid SMILES."""
        invalid_smiles = "invalid_smiles_string"
        fp = smiles_to_obabel_fingerprint(invalid_smiles, "ECFP4", timeout=10)
        
        assert fp is None, "Invalid SMILES should return None."

    @pytest.mark.skipif(not check_obabel_available(), reason="Open Babel not available")
    def test_empty_smiles(self):
        """Test handling of empty SMILES."""
        fp = smiles_to_obabel_fingerprint("", "ECFP4", timeout=10)
        assert fp is None, "Empty SMILES should return None."

        fp = smiles_to_obabel_fingerprint("   ", "ECFP4", timeout=10)
        assert fp is None, "Whitespace-only SMILES should return None."

    @pytest.mark.skipif(not check_obabel_available(), reason="Open Babel not available")
    def test_generate_fingerprints_batch(self):
        """Test batch fingerprint generation."""
        smiles_list = ["CCO", "CCCO", "CCCCO"]  # Ethanol, Propanol, Butanol
        df, errors = generate_fingerprints(smiles_list, fingerprint_types=["ECFP4"], timeout_per_mol=10)
        
        assert not df.empty, "DataFrame should not be empty."
        assert 'original_index' in df.columns, "DataFrame should have 'original_index' column."
        assert 'smiles' in df.columns, "DataFrame should have 'smiles' column."
        assert 'ECFP4_fp' in df.columns, "DataFrame should have 'ECFP4_fp' column."
        assert len(errors) == 0, "There should be no errors for valid SMILES."

    @pytest.mark.skipif(not check_obabel_available(), reason="Open Babel not available")
    def test_generate_fingerprints_with_errors(self):
        """Test batch fingerprint generation with some invalid SMILES."""
        smiles_list = ["CCO", "invalid", "CCCO"]
        df, errors = generate_fingerprints(smiles_list, fingerprint_types=["ECFP4"], timeout_per_mol=10)
        
        # Should have generated for valid ones
        assert not df.empty, "DataFrame should not be empty."
        # Should have errors for invalid one
        assert len(errors) > 0, "There should be errors for invalid SMILES."
        # Check that the number of rows corresponds to valid SMILES
        valid_count = sum(1 for s in smiles_list if s and isinstance(s, str) and len(s.strip()) > 0)
        assert len(df) == valid_count, f"DataFrame should have {valid_count} rows."

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
