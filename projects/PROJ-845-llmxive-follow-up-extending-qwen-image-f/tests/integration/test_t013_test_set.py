"""
Integration test for Task T013: Generalization Set Generation.
Verifies that the test set is generated, is distinct from training sets,
and meets the size requirement.
"""
import os
import sys
import csv
import hashlib
import tempfile
import shutil
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from generators.generate_test_set import compute_structure_hash, load_existing_hashes, main as test_set_main
from generators.save_datasets import main as save_datasets_main

class TestT013GeneralizationSet(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, "data", "raw")
        os.makedirs(self.data_dir, exist_ok=True)
        self.test_set_path = os.path.join(self.data_dir, "test_set.csv")
        
        # Create dummy training files to simulate existing data
        self._create_dummy_training_files()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _create_dummy_training_files(self):
        """Create dummy high, low, target CSVs with known hashes."""
        dummy_data = [
            ("high_entropy.csv", ["P", "Q"], ["AND"]),
            ("low_entropy.csv", ["A"], ["OR"]),
            ("target_specific.csv", ["X", "Y"], ["IMPLIES"])
        ]
        
        for filename, premises, operators in dummy_data:
            path = os.path.join(self.data_dir, filename)
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'premises', 'operators', 'solution', 'entropy_level', 'structure_hash', 'set_type', 'metadata'])
                writer.writeheader()
                h = compute_structure_hash(premises, operators)
                writer.writerow({
                    'id': 'dummy',
                    'premises': ';'.join(premises),
                    'operators': ';'.join(operators),
                    'solution': 'dummy',
                    'entropy_level': 'dummy',
                    'structure_hash': h,
                    'set_type': 'dummy',
                    'metadata': '{}'
                })

    def test_t013_generates_distinct_test_set(self):
        """Test that T013 generates a test set with distinct structure hashes."""
        # Run the dataset generation first to ensure training files exist
        # (We already created dummy ones, but let's run the logic to be sure)
        
        # Run T013 logic
        # We need to mock sys.argv for the main function
        original_argv = sys.argv
        try:
            sys.argv = [
                'test_t013',
                '--input-dir', self.data_dir,
                '--output-file', self.test_set_path,
                '--count', '50', # Small count for speed
                '--seed', '12345'
            ]
            test_set_main()
        finally:
            sys.argv = original_argv

        # Verify file exists
        self.assertTrue(os.path.exists(self.test_set_path), "Test set CSV was not created")

        # Load training hashes
        train_hashes = load_existing_hashes(self.data_dir)
        
        # Load test set and verify distinctness
        test_hashes = set()
        with open(self.test_set_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            self.assertGreaterEqual(len(rows), 50, "Test set has fewer than 50 samples")
            
            for row in rows:
                h = row['structure_hash']
                self.assertNotIn(h, train_hashes, f"Test set hash {h} found in training set!")
                self.assertEqual(row['set_type'], 'test_generalization', "set_type is not 'test_generalization'")
                test_hashes.add(h)

        # Verify all test hashes are unique within the test set
        self.assertEqual(len(test_hashes), len(rows), "Duplicate structure hashes found within test set")

    def test_t013_stratification(self):
        """Test that the test set contains samples of different entropy levels."""
        original_argv = sys.argv
        try:
            sys.argv = [
                'test_t013',
                '--input-dir', self.data_dir,
                '--output-file', self.test_set_path,
                '--count', '60', # Ensure we get at least some of each
                '--seed', '54321'
            ]
            test_set_main()
        finally:
            sys.argv = original_argv

        entropy_levels = set()
        with open(self.test_set_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entropy_levels.add(row['entropy_level'])

        # We expect at least 'high', 'low', 'target' based on the implementation
        self.assertIn('high', entropy_levels, "Missing 'high' entropy level in test set")
        self.assertIn('low', entropy_levels, "Missing 'low' entropy level in test set")
        self.assertIn('target', entropy_levels, "Missing 'target' entropy level in test set")

if __name__ == '__main__':
    unittest.main()