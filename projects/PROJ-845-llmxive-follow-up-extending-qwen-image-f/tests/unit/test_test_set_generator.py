import unittest
import tempfile
import os
import csv
import sys
from pathlib import Path

# Add project root to path if running from test directory
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from generators.test_set_generator import compute_structure_hash, load_existing_hashes, generate_unique_problem, write_test_set_csv
from models.synthetic_problem import SyntheticProblem

class TestTestSetGenerator(unittest.TestCase):

    def test_compute_structure_hash(self):
        """Test that structure hash is deterministic and unique for different structures."""
        premises1 = ["A", "B"]
        operators1 = ["AND"]
        premises2 = ["A", "B"]
        operators2 = ["OR"]
        
        hash1 = compute_structure_hash(premises1, operators1)
        hash2 = compute_structure_hash(premises2, operators2)
        hash3 = compute_structure_hash(premises1, operators1)
        
        self.assertEqual(hash1, hash3, "Same inputs should produce same hash")
        self.assertNotEqual(hash1, hash2, "Different operators should produce different hash")

    def test_load_existing_hashes(self):
        """Test loading hashes from a mock CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'structure_hash', 'other'])
            writer.writeheader()
            writer.writerow({'id': '1', 'structure_hash': 'hash1', 'other': 'x'})
            writer.writerow({'id': '2', 'structure_hash': 'hash2', 'other': 'y'})
            temp_path = f.name

        try:
            hashes = load_existing_hashes([temp_path])
            self.assertIn('hash1', hashes)
            self.assertIn('hash2', hashes)
            self.assertEqual(len(hashes), 2)
        finally:
            os.unlink(temp_path)

    def test_generate_unique_problem(self):
        """Test that generated problems are distinct from existing hashes."""
        existing_hashes = {'fixed_hash_1', 'fixed_hash_2'}
        
        # Generate a few problems
        problems = []
        for _ in range(5):
            p = generate_unique_problem(existing_hashes, max_attempts=100)
            if p:
                problems.append(p)
                structure_hash = compute_structure_hash(p.premises, p.operators)
                existing_hashes.add(structure_hash)
        
        # Verify all generated problems have unique hashes not in original set
        generated_hashes = [compute_structure_hash(p.premises, p.operators) for p in problems]
        
        for h in generated_hashes:
            self.assertNotIn(h, {'fixed_hash_1', 'fixed_hash_2'}, "Generated hash should not be in original set")
        
        # Verify no duplicates among generated
        self.assertEqual(len(generated_hashes), len(set(generated_hashes)), "Generated hashes should be unique")

    def test_write_test_set_csv(self):
        """Test writing problems to CSV."""
        problems = [
            SyntheticProblem(id="1", premises=["A"], operators=["AND"], solution="A", entropy_level="High", metadata={}),
            SyntheticProblem(id="2", premises=["B"], operators=["OR"], solution="B", entropy_level="Low", metadata={})
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name

        try:
            write_test_set_csv(problems, temp_path)
            
            self.assertTrue(os.path.exists(temp_path))
            with open(temp_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['set_type'], 'test_generalization')
            self.assertEqual(rows[0]['structure_hash'], compute_structure_hash(["A"], ["AND"]))
        finally:
            os.unlink(temp_path)

if __name__ == '__main__':
    unittest.main()
