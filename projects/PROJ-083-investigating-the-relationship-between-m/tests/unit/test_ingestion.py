"""
Unit tests for EAS pattern matching (T009).

This test verifies the is_eas_reaction function with known examples.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.ingestion import is_eas_reaction

def test_eas_pattern_benzene_nitration():
    """Test a known EAS reaction: Nitration of benzene."""
    # Benzene + HNO3 -> Nitrobenzene + H2O
    # Simplified SMILES: c1ccccc1.[N+](=O)[O-]>>c1ccc(cc1)[N+](=O)[O-]
    reaction_smiles = "c1ccccc1.[N+](=O)[O-]>>c1ccc(cc1)[N+](=O)[O-]"
    assert is_eas_reaction(reaction_smiles) is True

def test_eas_pattern_toluene_chlorination():
    """Test a known EAS reaction: Chlorination of toluene."""
    # Toluene + Cl2 -> Chlorotoluene + HCl
    reaction_smiles = "Cc1ccccc1.Cl>>Cc1ccc(Cl)cc1.Cl"
    assert is_eas_reaction(reaction_smiles) is True

def test_non_eas_reaction():
    """Test a non-EAS reaction: Aliphatic substitution."""
    # Ethane + Cl2 -> Chloroethane (not aromatic)
    reaction_smiles = "CC.Cl>>CCCl.Cl"
    assert is_eas_reaction(reaction_smiles) is False

def test_malformed_smiles():
    """Test malformed SMILES."""
    assert is_eas_reaction("invalid_smiles") is False
    assert is_eas_reaction("") is False

if __name__ == "__main__":
    test_eas_pattern_benzene_nitration()
    test_eas_pattern_toluene_chlorination()
    test_non_eas_reaction()
    test_malformed_smiles()
    print("All unit tests passed.")
