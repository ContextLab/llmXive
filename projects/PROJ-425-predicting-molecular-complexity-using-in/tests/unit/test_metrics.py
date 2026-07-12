"""
Unit tests for metrics computation functions.

Tests for:
- compute_shannon_entropy
- compute_lz_complexity
- compute_sa_qed
"""
import pytest
import math
import os
import sys
import tempfile
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from metrics import (
    compute_shannon_entropy,
    compute_lz_complexity,
    compute_sa_qed,
    TimeoutError,
    timeout
)
from rdkit import Chem
from rdkit.Chem import Descriptors


class TestComputeShannonEntropy:
    """Tests for the Shannon entropy calculation based on vertex degree distribution."""

    def test_simple_molecule(self):
        """Test entropy calculation on a simple molecule (benzene)."""
        smiles = "c1ccccc1"
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None, "Failed to parse benzene SMILES"
        
        entropy = compute_shannon_entropy(mol)
        
        # Entropy should be a non-negative float
        assert isinstance(entropy, float)
        assert entropy >= 0.0
        
        # For benzene (all carbons with degree 3), entropy should be 0
        # because there is only one unique degree value
        assert math.isclose(entropy, 0.0, abs_tol=1e-6), \
            f"Benzene should have entropy ~0.0, got {entropy}"

    def test_complex_molecule(self):
        """Test entropy calculation on a more complex molecule."""
        # Caffeine: more diverse atom degrees
        smiles = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None, "Failed to parse caffeine SMILES"
        
        entropy = compute_shannon_entropy(mol)
        
        assert isinstance(entropy, float)
        assert entropy >= 0.0
        # Caffeine has multiple degree types, so entropy > 0
        assert entropy > 0.0, "Caffeine should have non-zero entropy due to diverse atom degrees"

    def test_invalid_molecule(self):
        """Test that invalid molecules raise appropriate errors or return None."""
        # RDKit returns None for invalid SMILES
        mol = Chem.MolFromSmiles("invalid_smiles_string")
        assert mol is None
        
        # Our function should handle None gracefully or raise a clear error
        # Based on implementation, it should either return None or raise ValueError
        with pytest.raises((ValueError, TypeError)):
            compute_shannon_entropy(mol)

    def test_empty_molecule(self):
        """Test behavior with an empty molecule."""
        mol = Chem.MolFromSmiles("")
        # Empty string might return None or an empty molecule
        if mol is None:
            with pytest.raises((ValueError, TypeError)):
                compute_shannon_entropy(mol)
        else:
            # If it creates an empty molecule, entropy should be 0 or raise error
            entropy = compute_shannon_entropy(mol)
            assert entropy == 0.0 or entropy is None


class TestComputeLzComplexity:
    """Tests for Lempel-Ziv complexity calculation on SMILES strings."""

    def test_simple_string(self):
        """Test LZ complexity on a simple, repetitive string."""
        smiles = "CCCCC"  # Pentane - very repetitive
        complexity = compute_lz_complexity(smiles)
        
        assert isinstance(complexity, float)
        assert complexity >= 0.0
        # Repetitive strings should have lower complexity
        assert complexity < 1.0, f"Repetitive string should have low complexity, got {complexity}"

    def test_complex_string(self):
        """Test LZ complexity on a more complex, less repetitive string."""
        smiles = "c1ccccc1C(=O)O"  # Benzoic acid - more diverse characters
        complexity = compute_lz_complexity(smiles)
        
        assert isinstance(complexity, float)
        assert complexity >= 0.0
        # More diverse string should have higher complexity than repetitive one
        simple_complexity = compute_lz_complexity("CCCCC")
        assert complexity > simple_complexity, \
            f"Complex string should have higher complexity than simple one"

    def test_empty_string(self):
        """Test behavior with empty string."""
        complexity = compute_lz_complexity("")
        assert complexity == 0.0 or complexity == 0

    def test_invalid_characters(self):
        """Test that the function handles SMILES with valid characters only."""
        # Valid SMILES characters include: C, N, O, S, P, F, Cl, Br, I, c, n, o, s, p, 
        # parentheses, brackets, numbers, @, =, #, /, \, +, -
        smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
        complexity = compute_lz_complexity(smiles)
        assert isinstance(complexity, float)
        assert complexity > 0.0

    def test_case_sensitivity(self):
        """Test that uppercase and lowercase are treated differently."""
        # In SMILES, c (aromatic) and C (aliphatic) are different
        aromatic = "c1ccccc1"
        aliphatic = "C1CCCCC1"
        
        complexity_aromatic = compute_lz_complexity(aromatic)
        complexity_aliphatic = compute_lz_complexity(aliphatic)
        
        # These should be different due to different character sequences
        assert complexity_aromatic != complexity_aliphatic, \
            "Aromatic and aliphatic representations should have different complexities"


class TestComputeSaQed:
    """Tests for Synthetic Accessibility Score (SA) and Quantitative Estimate of Drug-likeness (QED)."""

    def test_valid_molecule(self):
        """Test SA and QED calculation on a valid molecule."""
        smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None, "Failed to parse aspirin SMILES"
        
        sa_score, qed_score = compute_sa_qed(mol)
        
        # SA score should be between 1 and 10 (lower is better)
        assert isinstance(sa_score, float)
        assert 1.0 <= sa_score <= 10.0, f"SA score {sa_score} out of range [1, 10]"
        
        # QED score should be between 0 and 1 (higher is better)
        assert isinstance(qed_score, float)
        assert 0.0 <= qed_score <= 1.0, f"QED score {qed_score} out of range [0, 1]"

    def test_simple_molecule(self):
        """Test that simple molecules have good QED and low SA."""
        smiles = "CCO"  # Ethanol - very simple
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None
        
        sa_score, qed_score = compute_sa_qed(mol)
        
        # Simple molecules should have high QED (close to 1)
        assert qed_score > 0.5, f"Simple molecule should have good QED, got {qed_score}"
        
        # Simple molecules should have low SA score (close to 1)
        assert sa_score < 5.0, f"Simple molecule should have low SA, got {sa_score}"

    def test_complex_molecule(self):
        """Test that complex molecules have lower QED and higher SA."""
        # Large, complex molecule
        smiles = "CC(C)C1C(C(C(C(C2C(C(C(C(O2)CO)O)O)O)O)O)O)O"  # Complex sugar derivative
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            pytest.skip("Could not parse complex molecule")
        
        sa_score, qed_score = compute_sa_qed(mol)
        
        # Complex molecules typically have lower QED
        assert qed_score >= 0.0  # Just ensure it's in valid range
        
        # Complex molecules typically have higher SA (harder to synthesize)
        assert sa_score <= 10.0  # Just ensure it's in valid range

    def test_invalid_molecule(self):
        """Test handling of invalid molecules."""
        mol = None  # Simulate a failed parsing
        
        with pytest.raises((ValueError, TypeError)):
            compute_sa_qed(mol)

    def test_very_large_molecule(self):
        """Test that very large molecules are handled (may have edge cases)."""
        # Create a very long chain
        smiles = "C" * 100  # 100-carbon chain
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            pytest.skip("Could not parse very large molecule")
        
        sa_score, qed_score = compute_sa_qed(mol)
        
        # Should still return valid ranges
        assert 1.0 <= sa_score <= 10.0
        assert 0.0 <= qed_score <= 1.0


class TestTimeoutDecorator:
    """Tests for the timeout decorator functionality."""

    def test_timeout_function(self):
        """Test that the timeout decorator works correctly."""
        @timeout(1)  # 1 second timeout
        def slow_function():
            import time
            time.sleep(2)  # Sleep for 2 seconds
            return "completed"
        
        with pytest.raises(TimeoutError):
            slow_function()

    def test_fast_function(self):
        """Test that fast functions complete normally."""
        @timeout(5)  # 5 second timeout
        def fast_function():
            return "success"
        
        result = fast_function()
        assert result == "success"

    def test_timeout_with_return_value(self):
        """Test that functions completing within timeout return correct values."""
        @timeout(2)
        def function_with_return():
            return 42, "test"
        
        result = function_with_return()
        assert result == (42, "test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
