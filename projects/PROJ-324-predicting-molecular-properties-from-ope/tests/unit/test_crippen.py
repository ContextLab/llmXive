"""
Unit tests for Crippen's atomic contribution calculation.

This module validates the implementation of Crippen's additive fragment model
for predicting molecular properties (logP, solubility, boiling point).
It tests the core logic of atomic contributions against known chemical rules
and verifies the calculation pipeline.
"""

import pytest
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors
from pathlib import Path
import sys

# Add project root to path for imports if running standalone
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.models.baseline import calculate_crippen_logp, get_atomic_contributions


class TestCrippenAtomicContributions:
    """Test suite for Crippen's atomic contribution logic."""

    def test_benzene_logp_calculation(self):
        """
        Test logP calculation for Benzene (C6H6).
        Expected logP (experimental) is approx 2.13.
        Crippen's model should yield a value close to this.
        """
        smiles = "c1ccccc1"
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None, "Failed to parse Benzene SMILES"

        calculated_logp = calculate_crippen_logp(mol)
        expected_logp = 2.13
        
        # Allow a reasonable margin of error for the additive model
        assert abs(calculated_logp - expected_logp) < 0.5, \
            f"Benzene logP mismatch: calculated {calculated_logp:.2f}, expected ~{expected_logp}"

    def test_water_logp_calculation(self):
        """
        Test logP calculation for Water (O).
        Expected logP is approx -1.38 (highly hydrophilic).
        """
        smiles = "O"
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None, "Failed to parse Water SMILES"

        calculated_logp = calculate_crippen_logp(mol)
        expected_logp = -1.38

        assert calculated_logp < 0, "Water should have negative logP"
        assert abs(calculated_logp - expected_logp) < 0.5, \
            f"Water logP mismatch: calculated {calculated_logp:.2f}, expected ~{expected_logp}"

    def test_octanol_logp_calculation(self):
        """
        Test logP calculation for Octanol (C8H18O).
        Expected logP is approx 2.9.
        """
        smiles = "CCCCCCCCO"
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None, "Failed to parse Octanol SMILES"

        calculated_logp = calculate_crippen_logp(mol)
        expected_logp = 2.9

        assert calculated_logp > 1.0, "Octanol should be lipophilic"
        assert abs(calculated_logp - expected_logp) < 0.6, \
            f"Octanol logP mismatch: calculated {calculated_logp:.2f}, expected ~{expected_logp}"

    def test_atomic_contributions_structure(self):
        """
        Test that get_atomic_contributions returns the expected structure.
        """
        smiles = "CCO"  # Ethanol
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None

        contributions = get_atomic_contributions(mol)
        
        assert isinstance(contributions, list), "Contributions must be a list"
        assert len(contributions) == mol.GetNumAtoms(), \
            f"Expected {mol.GetNumAtoms()} contributions, got {len(contributions)}"
        
        for contrib in contributions:
            assert isinstance(contrib, dict), "Each contribution must be a dict"
            assert "atom_idx" in contrib, "Missing 'atom_idx'"
            assert "element" in contrib, "Missing 'element'"
            assert "type" in contrib, "Missing 'type'"
            assert "logp_contrib" in contrib, "Missing 'logp_contrib'"
            assert isinstance(contrib["logp_contrib"], (int, float)), \
                "logp_contrib must be numeric"

    def test_invalid_molecule_handling(self):
        """
        Test behavior when an invalid SMILES is provided.
        """
        mol = None
        try:
            result = calculate_crippen_logp(mol)
            # Should raise an error or return None, not crash silently
            assert False, "Should have raised an error for None molecule"
        except (TypeError, AttributeError):
            # Expected behavior
            pass

    def test_additivity_property(self):
        """
        Verify that the total logP is the sum of atomic contributions.
        This validates the core 'additive' assumption of the Crippen model.
        """
        smiles = "CCO"  # Ethanol
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None

        total_logp = calculate_crippen_logp(mol)
        contributions = get_atomic_contributions(mol)
        
        sum_contribs = sum(c["logp_contrib"] for c in contributions)
        
        # Allow for minor floating point differences
        assert np.isclose(total_logp, sum_contribs, rtol=1e-5), \
            f"Additivity failed: Total {total_logp} != Sum {sum_contribs}"

    def test_carbon_chain_additivity(self):
        """
        Test that adding a CH2 group increases logP by a consistent amount.
        Methane -> Ethane -> Propane
        """
        chain_smiles = ["C", "CC", "CCC"]
        logps = []
        
        for s in chain_smiles:
            mol = Chem.MolFromSmiles(s)
            logps.append(calculate_crippen_logp(mol))

        # The difference between consecutive alkanes should be roughly constant
        # (approx 0.5 to 0.6 per CH2 group in Crippen's model)
        diff1 = logps[1] - logps[0]
        diff2 = logps[2] - logps[1]
        
        assert abs(diff1 - diff2) < 0.1, \
            f"Additivity across chain length failed: diffs {diff1:.2f} vs {diff2:.2f}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])