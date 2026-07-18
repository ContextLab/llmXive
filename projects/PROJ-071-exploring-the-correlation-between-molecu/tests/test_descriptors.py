import pytest
import pandas as pd
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from descriptors import calculate_descriptors_for_molecule, calculate_descriptors_batch, AtomValenceException, log_error_to_file

class TestDescriptors:
    def test_tpsa_wiener_zagreb_aspirin(self):
        """
        Unit test for RDKit descriptor calculation.
        Aspirin: CC(=O)OC1=CC=CC=C1C(=O)O
        Expected TPSA: ~63.6
        """
        smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
        try:
            desc = calculate_descriptors_for_molecule(smiles)
            
            # Check TPSA (approx 63.6)
            assert 'tpsa' in desc
            assert 60 < desc['tpsa'] < 70, f"TPSA {desc['tpsa']} out of expected range for Aspirin"
            
            # Check Wiener Index (must be a number)
            assert 'wiener_index' in desc
            assert isinstance(desc['wiener_index'], (int, float))
            assert desc['wiener_index'] > 0
            
            # Check Zagreb Index
            assert 'zagreb_index' in desc
            assert isinstance(desc['zagreb_index'], (int, float))
            assert desc['zagreb_index'] > 0
            
            # Check other descriptors
            assert 'rotatable_bonds' in desc
            assert 'mw' in desc
            assert 'aromatic_rings' in desc
            
        except AtomValenceException:
            pytest.fail("Aspirin should not raise AtomValenceException")

    def test_invalid_smiles_handling(self):
        """
        Test that invalid SMILES raise AtomValenceException.
        """
        invalid_smiles = "invalid_smiles_string_123"
        with pytest.raises(AtomValenceException):
            calculate_descriptors_for_molecule(invalid_smiles)

    def test_batch_processing_with_errors(self, tmp_path):
        """
        Test batch processing excludes invalid molecules and logs errors.
        """
        data = {
            'smiles': ['CCO', 'invalid', 'CC(=O)O', ''],
            'id': [1, 2, 3, 4]
        }
        df = pd.DataFrame(data)
        
        log_path = str(tmp_path / "errors.log")
        
        result_df = calculate_descriptors_batch(df, log_path=log_path)
        
        # Should have 2 valid rows (Ethanol and Acetic Acid)
        assert len(result_df) == 2
        
        # Check log file exists and contains error
        assert Path(log_path).exists()
        log_content = Path(log_path).read_text()
        assert "invalid" in log_content or "invalid_smiles_string_123" in log_content
        assert "Row 1" in log_content or "index 1" in log_content.lower()