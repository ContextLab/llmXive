"""
Unit tests for the logic generator module.

These tests verify that the logic proof generator:
1. Creates valid proofs
2. Handles retry logic correctly
3. Produces reproducible results with seeds
"""

import pytest
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from generators.logic_generator import (
    LogicProofGenerator,
    generate_logic_proofs,
    MAX_RETRIES
)
from sympy import symbols, Implies, And, simplify_logic


class TestLogicProofGenerator:
    """Test cases for the LogicProofGenerator class."""

    def test_initialization(self):
        """Test that the generator initializes correctly."""
        generator = LogicProofGenerator()
        assert generator is not None

        generator_with_seed = LogicProofGenerator(seed=42)
        assert generator_with_seed is not None

    def test_symbol_generation(self):
        """Test that symbols are generated correctly."""
        generator = LogicProofGenerator()
        symbols_list = generator._generate_symbols(5)

        assert len(symbols_list) == 5
        assert all(isinstance(s, type(symbols('P'))) for s in symbols_list)

    def test_axiom_creation(self):
        """Test that axioms are created as valid logical expressions."""
        generator = LogicProofGenerator()
        symbols_list = generator._generate_symbols(3)

        axiom = generator._create_axiom(symbols_list)
        assert axiom is not None
        # Axioms should be valid SymPy expressions
        assert hasattr(axiom, 'free_symbols')

    def test_proof_generation_validity(self):
        """Test that generated proofs are logically valid."""
        generator = LogicProofGenerator(seed=42)
        proof = generator.generate_proof()

        assert proof is not None, "Proof generation should succeed"
        assert proof['valid'] is True, "Proof should be marked as valid"
        assert 'steps' in proof, "Proof should contain steps"
        assert len(proof['steps']) > 0, "Proof should have at least one step"

    def test_proof_generation_with_retry(self):
        """Test that retry logic works for invalid generations."""
        # This test verifies the retry mechanism doesn't cause infinite loops
        generator = LogicProofGenerator()

        # Generate multiple proofs to ensure retry logic works
        for i in range(5):
            proof = generator.generate_proof()
            assert proof is not None or i < MAX_RETRIES

    def test_dataset_generation(self):
        """Test that dataset generation creates multiple valid proofs."""
        generator = LogicProofGenerator(seed=123)
        proofs = generator.generate_dataset(count=3)

        assert len(proofs) == 3, "Should generate exactly 3 proofs"
        for proof in proofs:
            assert proof['valid'] is True

    def test_reproducibility_with_seed(self):
        """Test that results are reproducible with the same seed."""
        proofs1 = generate_logic_proofs(count=2, seed=999)
        proofs2 = generate_logic_proofs(count=2, seed=999)

        # The proofs should be identical
        assert len(proofs1) == len(proofs2)
        for p1, p2 in zip(proofs1, proofs2):
            assert p1['target'] == p2['target']
            assert len(p1['steps']) == len(p2['steps'])

    def test_proof_contains_expected_fields(self):
        """Test that proofs contain all required fields."""
        generator = LogicProofGenerator()
        proof = generator.generate_proof()

        required_fields = ['axioms', 'target', 'steps', 'valid']
        for field in required_fields:
            assert field in proof, f"Proof should contain '{field}'"

    def test_step_justifications(self):
        """Test that proof steps have valid justifications."""
        generator = LogicProofGenerator()
        proof = generator.generate_proof()

        valid_justifications = ['Axiom', 'Derived', 'Valid Implication', 'Target Derived']
        for step in proof['steps']:
            assert 'justification' in step
            assert step['justification'] in valid_justifications

    def test_empty_proof_handling(self):
        """Test that the validator handles edge cases."""
        generator = LogicProofGenerator()
        assert not generator._validate_proof([])
        assert not generator._validate_proof(None)


class TestLogicProofGenerationFunction:
    """Test cases for the convenience function."""

    def test_generate_logic_proofs_basic(self):
        """Test the basic functionality of generate_logic_proofs."""
        proofs = generate_logic_proofs(count=3, seed=42)

        assert len(proofs) == 3
        assert all(p['valid'] for p in proofs)

    def test_generate_logic_proofs_custom_params(self):
        """Test generate_logic_proofs with custom parameters."""
        proofs = generate_logic_proofs(
            count=2,
            seed=777,
            num_axioms=3,
            proof_length=5
        )

        assert len(proofs) == 2
        for proof in proofs:
            assert len(proof['axioms']) == 3

    def test_generate_logic_proofs_zero_count(self):
        """Test generate_logic_proofs with count=0."""
        proofs = generate_logic_proofs(count=0)
        assert len(proofs) == 0


class TestProofValidation:
    """Test cases for proof validation logic."""

    def test_valid_proof_detection(self):
        """Test that valid proofs are correctly identified."""
        generator = LogicProofGenerator()
        proof = generator.generate_proof()

        # The proof should pass validation
        assert generator._validate_proof(proof['steps']) is True

    def test_invalid_step_detection(self):
        """Test that invalid steps are detected."""
        generator = LogicProofGenerator()

        # Create a fake invalid proof
        from sympy import symbols
        p, q = symbols('P Q')

        invalid_steps = [
            {"step": 1, "statement": str(p), "justification": "Axiom", "expression": p},
            {"step": 2, "statement": str(q), "justification": "Derived", "expression": q}
        ]

        # This should fail validation since q doesn't follow from p
        assert generator._validate_proof(invalid_steps) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
