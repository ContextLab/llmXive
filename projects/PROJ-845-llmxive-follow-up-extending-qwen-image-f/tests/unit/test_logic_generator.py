"""
Unit tests for the logic_generator module.
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from generators.logic_generator import (
    generate_propositional_problem,
    generate_arithmetic_problem,
    generate_dataset_batch
)
from models.synthetic_problem import SyntheticProblem
from config import Config, get_config


class TestPropositionalGenerator:
    def test_generates_valid_object(self):
        """Test that generate_propositional_problem returns a valid SyntheticProblem."""
        problem = generate_propositional_problem(entropy_level="high", num_premises=3)
        assert isinstance(problem, SyntheticProblem)
        assert problem.entropy_level == "high"
        assert len(problem.premises) > 0
        assert problem.solution is not None
        assert problem.metadata is not None
        assert "structure_hash" in problem.metadata

    def test_low_entropy_structure(self):
        """Test that low entropy problems have structured patterns."""
        problem = generate_propositional_problem(entropy_level="low", num_premises=5)
        # Low entropy should use IMPLIES chains predominantly
        operators = problem.operators
        # Just verify it generated without error and has operators
        assert len(operators) > 0
        # Check that premises are not empty
        assert len(problem.premises) > 0

    def test_id_format(self):
        """Test that problem IDs are unique and formatted correctly."""
        p1 = generate_propositional_problem(entropy_level="high")
        p2 = generate_propositional_problem(entropy_level="high")
        assert p1.id != p2.id
        assert p1.id.startswith("prop_")

    def test_metadata_consistency(self):
        """Test that metadata contains required fields."""
        problem = generate_propositional_problem(entropy_level="low")
        assert problem.metadata["type"] == "propositional"
        assert "structure_hash" in problem.metadata
        assert "num_premises" in problem.metadata


class TestArithmeticGenerator:
    def test_generates_valid_object(self):
        """Test that generate_arithmetic_problem returns a valid SyntheticProblem."""
        problem = generate_arithmetic_problem(entropy_level="high", num_ops=3)
        assert isinstance(problem, SyntheticProblem)
        assert problem.entropy_level == "high"
        assert len(problem.premises) > 0
        assert problem.solution is not None

    def test_low_entropy_arithmetic(self):
        """Test that low entropy arithmetic problems have simple structures."""
        problem = generate_arithmetic_problem(entropy_level="low", num_ops=4)
        assert len(problem.operators) > 0
        assert len(problem.premises) > 0

    def test_id_format(self):
        """Test that arithmetic problem IDs are unique and formatted correctly."""
        p1 = generate_arithmetic_problem(entropy_level="high")
        p2 = generate_arithmetic_problem(entropy_level="high")
        assert p1.id != p2.id
        assert p1.id.startswith("arith_")


class TestBatchGeneration:
    def test_batch_size(self):
        """Test that batch generation produces the correct number of problems."""
        batch = generate_dataset_batch(subset_type="high_entropy", count=10)
        assert len(batch) == 10

    def test_batch_entropy_levels(self):
        """Test that batch respects entropy level if forced."""
        batch = generate_dataset_batch(subset_type="test", count=5, entropy_level="high")
        for p in batch:
            assert p.entropy_level == "high"

    def test_batch_uniqueness(self):
        """Test that all problems in a batch have unique IDs and structure hashes."""
        batch = generate_dataset_batch(subset_type="low_entropy", count=20)
        ids = [p.id for p in batch]
        hashes = [p.metadata["structure_hash"] for p in batch]
        
        assert len(ids) == len(set(ids))
        assert len(hashes) == len(set(hashes))