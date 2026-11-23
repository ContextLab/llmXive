"""
Unit tests for Task T013: Distinct Generalization Set generation.
"""
import os
import sys
import csv
import json
import tempfile
import shutil
from pathlib import Path
import unittest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from generators.generate_test_set import compute_structure_hash, load_existing_hashes
from models.synthetic_problem import SyntheticProblem

class TestT013Distinctness(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.training_csv = os.path.join(self.temp_dir, 'high_entropy.csv')
        self.test_csv = os.path.join(self.temp_dir, 'test_set.csv')
        
        # Create a mock training CSV
        with open(self.training_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'premises', 'operators', 'solution', 'entropy_level', 'structure_hash', 'set_type', 'metadata'])
            # Write a known problem
            p1 = SyntheticProblem(
                id="train_1",
                premises=["A", "B"],
                operators=["AND"],
                solution="A and B",
                entropy_level="High",
                metadata={}
            )
            h1 = compute_structure_hash(p1.premises, p1.operators)
            writer.writerow([p1.id, ";".join(p1.premises), ";".join(p1.operators), p1.solution, p1.entropy_level, h1, "train", "{}"])
        
        self.h1 = h1

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_compute_structure_hash_consistency(self):
        """Test that the same premises/operators produce the same hash."""
        p1 = SyntheticProblem(id="1", premises=["A"], operators=["NOT"], solution="Not A", entropy_level="High", metadata={})
        p2 = SyntheticProblem(id="2", premises=["A"], operators=["NOT"], solution="Not A", entropy_level="Low", metadata={})
        
        h1 = compute_structure_hash(p1.premises, p1.operators)
        h2 = compute_structure_hash(p2.premises, p2.operators)
        
        self.assertEqual(h1, h2)

    def test_compute_structure_hash_differs(self):
        """Test that different premises produce different hashes."""
        h1 = compute_structure_hash(["A"], ["NOT"])
        h2 = compute_structure_hash(["B"], ["NOT"])
        
        self.assertNotEqual(h1, h2)

    def test_load_existing_hashes(self):
        """Test loading hashes from a CSV."""
        hashes = load_existing_hashes(self.training_csv)
        self.assertIn(self.h1, hashes)
        self.assertEqual(len(hashes), 1)

    def test_hash_not_in_set(self):
        """Test that a new hash is not in the loaded set."""
        hashes = load_existing_hashes(self.training_csv)
        new_hash = compute_structure_hash(["C"], ["OR"])
        self.assertNotIn(new_hash, hashes)

if __name__ == '__main__':
    unittest.main()