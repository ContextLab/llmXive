"""
Unit tests for molecular complexity metrics.
"""
import pytest
import sys
from pathlib import Path

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from metrics import (
    calculate_shannon_entropy,
    calculate_lzma_length,
    calculate_sa_score,
    calculate_qed_score,
    calculate_molecular_weight,
    calculate_atom_count,
)


class TestShannonEntropy:
    """Tests for Shannon entropy calculation."""

    def test_shannon_entropy_returns_positive_float(self):
        """
        Test that calculate_shannon_entropy returns a positive float.
        
        Input: smiles="CCO" (Ethanol)
        Assertion: result > 0 and isinstance(result, float)
        """
        smiles = "CCO"
        result = calculate_shannon_entropy(smiles)
        
        assert result > 0, f"Shannon entropy should be positive for valid SMILES, got {result}"
        assert isinstance(result, float), f"Shannon entropy should be a float, got {type(result)}"

    def test_shannon_entropy_empty_string(self):
        """Test behavior with empty string (should raise or return 0)."""
        with pytest.raises((ValueError, ZeroDivisionError)):
            calculate_shannon_entropy("")

    def test_shannon_entropy_simple_molecule(self):
        """Test with a simple molecule like methane."""
        result = calculate_shannon_entropy("C")
        assert result >= 0
        assert isinstance(result, float)


class TestLzmaLength:
    """Tests for LZMA compression length calculation."""

    def test_lzma_length_returns_integer(self):
        """
        Test that calculate_lzma_length returns an integer.
        
        Input: smiles="CCO" (Ethanol)
        Assertion: isinstance(result, int) and result > 0
        """
        smiles = "CCO"
        result = calculate_lzma_length(smiles)
        
        assert isinstance(result, int), f"LZMA length should be an integer, got {type(result)}"
        assert result > 0, f"LZMA length should be positive for valid SMILES, got {result}"

    def test_lzma_length_simple_molecule(self):
        """Test with a simple molecule."""
        result = calculate_lzma_length("C")
        assert isinstance(result, int)
        assert result > 0


class TestSaAndQedScore:
    """Tests for SA and QED score calculations."""

    def test_sa_and_qed_return_valid_range(self):
        """
        Test that SA and QED scores return values in valid ranges.
        
        Input: smiles="CCO" (Ethanol)
        Assertion: 0.0 <= sa_score <= 10.0 and 0.0 <= qed_score <= 1.0
        """
        smiles = "CCO"
        
        sa_result = calculate_sa_score(smiles)
        qed_result = calculate_qed_score(smiles)
        
        assert 0.0 <= sa_result <= 10.0, f"SA score should be in [0, 10], got {sa_result}"
        assert 0.0 <= qed_result <= 1.0, f"QED score should be in [0, 1], got {qed_result}"
        
        assert isinstance(sa_result, float), f"SA score should be float, got {type(sa_result)}"
        assert isinstance(qed_result, float), f"QED score should be float, got {type(qed_result)}"

    def test_sa_score_complex_molecule(self):
        """Test SA score with a more complex molecule."""
        # A more complex molecule
        smiles = "CC(C)C1=CC=C(C=C1)C(C)C(=O)O"  # Ibuprofen
        result = calculate_sa_score(smiles)
        assert 0.0 <= result <= 10.0

    def test_qed_score_complex_molecule(self):
        """Test QED score with a more complex molecule."""
        smiles = "CC(C)C1=CC=C(C=C1)C(C)C(=O)O"  # Ibuprofen
        result = calculate_qed_score(smiles)
        assert 0.0 <= result <= 1.0


class TestMolecularWeight:
    """Tests for molecular weight calculation."""

    def test_molecular_weight_returns_positive(self):
        """Test that molecular weight is positive."""
        smiles = "CCO"
        result = calculate_molecular_weight(smiles)
        assert result > 0
        assert isinstance(result, float)

    def test_molecular_weight_ethanol(self):
        """Test molecular weight for ethanol (approx 46.07 g/mol)."""
        smiles = "CCO"
        result = calculate_molecular_weight(smiles)
        # Ethanol: C2H6O -> 2*12.01 + 6*1.008 + 16.00 ≈ 46.07
        assert 45.0 < result < 47.0


class TestAtomCount:
    """Tests for atom count calculation."""

    def test_atom_count_returns_integer(self):
        """Test that atom count returns an integer."""
        smiles = "CCO"
        result = calculate_atom_count(smiles)
        assert isinstance(result, int)
        assert result > 0

    def test_atom_count_ethanol(self):
        """Test atom count for ethanol (C2H6O -> 9 atoms)."""
        smiles = "CCO"
        result = calculate_atom_count(smiles)
        # Ethanol: 2 C + 6 H + 1 O = 9 atoms
        assert result == 9

    def test_atom_count_methane(self):
        """Test atom count for methane (CH4 -> 5 atoms)."""
        smiles = "C"
        result = calculate_atom_count(smiles)
        assert result == 5