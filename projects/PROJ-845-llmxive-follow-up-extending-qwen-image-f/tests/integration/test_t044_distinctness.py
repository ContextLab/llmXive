import os
import sys
import csv
import tempfile
import pytest
from pathlib import Path

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generators.test_set_generator import (
    compute_structure_hash, 
    load_existing_hashes, 
    generate_distinct_problem,
    write_test_set_csv
)
from models.synthetic_problem import SyntheticProblem

class TestT044DistinctnessVerification:
    """
    Tests for T044: Explicit hash-based distinctness verification.
    Ensures that the test set generator guarantees structural independence from training data.
    """

    def test_compute_structure_hash_consistency(self):
        """Test that the same premises/operators produce the same hash."""
        premises = ["A implies B", "B implies C"]
        operators = ["implies"]
        
        hash1 = compute_structure_hash(premises, operators)
        hash2 = compute_structure_hash(premises, operators)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_compute_structure_hash_differs_with_content(self):
        """Test that different premises produce different hashes."""
        premises1 = ["A implies B"]
        premises2 = ["A implies C"]
        operators = ["implies"]
        
        hash1 = compute_structure_hash(premises1, operators)
        hash2 = compute_structure_hash(premises2, operators)
        
        assert hash1 != hash2

    def test_generate_distinct_problem_enforces_uniqueness(self):
        """
        Test that generate_distinct_problem raises an error if it cannot find a unique structure,
        or successfully returns a unique one when possible.
        """
        # Create a small set of "existing" hashes
        existing_hashes = {
            "hash_12345",
            "hash_67890"
        }

        # We expect this to succeed because the generator has a vast space
        # and our existing set is tiny.
        # Note: This test relies on the generator actually producing new hashes.
        # In a real scenario, we might mock the generator, but here we test the logic.
        try:
            problem, new_hash = generate_distinct_problem(existing_hashes, max_attempts=100)
            
            # Verify the returned hash was not in the existing set
            assert new_hash not in existing_hashes
            
            # Verify the problem structure matches the hash
            computed = compute_structure_hash(problem.premises, problem.operators)
            assert computed == new_hash
            
        except RuntimeError as e:
            # If it fails, it means the generator is not diverse enough or the logic is broken
            pytest.fail(f"Failed to generate distinct problem: {e}")

    def test_load_existing_hashes_from_csv(self):
        """Test that load_existing_hashes correctly reads from a CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'premises', 'operators', 'solution', 'entropy_level', 'structure_hash', 'metadata'])
            writer.writeheader()
            writer.writerow({
                'id': '1', 'premises': 'A', 'operators': 'or', 'solution': 'B', 
                'entropy_level': 'high', 'structure_hash': 'fake_hash_1', 'metadata': '{}'
            })
            writer.writerow({
                'id': '2', 'premises': 'C', 'operators': 'and', 'solution': 'D', 
                'entropy_level': 'low', 'structure_hash': 'fake_hash_2', 'metadata': '{}'
            })
            temp_path = f.name

        try:
            hashes = load_existing_hashes([temp_path])
            assert 'fake_hash_1' in hashes
            assert 'fake_hash_2' in hashes
            assert len(hashes) == 2
        finally:
            os.unlink(temp_path)

    def test_full_generation_flow_distinctness(self):
        """
        Integration test: Generate a small training set, then generate a test set,
        and verify no structure hashes overlap.
        """
        # This is a simplified integration test. 
        # We manually create a "training" set with known hashes, then try to generate a test set.
        
        training_hashes = {
            "training_hash_1",
            "training_hash_2",
            "training_hash_3"
        }

        # Attempt to generate 5 distinct problems
        generated_problems = []
        generated_hashes = []
        
        for _ in range(5):
            problem, new_hash = generate_distinct_problem(training_hashes, max_attempts=1000)
            generated_problems.append(problem)
            generated_hashes.append(new_hash)
            training_hashes.add(new_hash) # Add to set to ensure next one is different too

        # Verify no overlap with original training hashes
        for h in generated_hashes:
            assert h not in {"training_hash_1", "training_hash_2", "training_hash_3"}

        # Verify all generated hashes are unique among themselves
        assert len(generated_hashes) == len(set(generated_hashes))