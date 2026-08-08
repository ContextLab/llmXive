"""
Integration test for T013: Test Set Generation.

Verifies that the test set generator:
1. Creates the output file.
2. Generates at least 500 samples.
3. Ensures structure_hash distinctness from training sets.
4. Stratifies by entropy level.
"""
import os
import sys
import csv
import tempfile
import shutil
import hashlib
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from generators.test_set_generator import (
    compute_structure_hash, 
    load_existing_hashes, 
    generate_unique_problem, 
    write_test_set_csv
)
from models.synthetic_problem import SyntheticProblem

class TestTestSetGeneration:
    
    def setup_method(self):
        """Create temporary directories and mock training files."""
        self.temp_dir = tempfile.mkdtemp()
        self.training_dir = os.path.join(self.temp_dir, 'training')
        self.output_dir = os.path.join(self.temp_dir, 'output')
        os.makedirs(self.training_dir)
        os.makedirs(self.output_dir)
        
        # Create mock training CSVs with known hashes
        self.training_files = []
        for i, name in enumerate(['high_entropy.csv', 'low_entropy.csv', 'target_specific.csv']):
            path = os.path.join(self.training_dir, name)
            self.training_files.append(path)
            
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'premises', 'operators', 'solution', 'entropy_level', 'structure_hash', 'set_type', 'metadata'])
                writer.writeheader()
                # Write 5 mock problems with distinct hashes
                for j in range(5):
                    premises = [f"P{i}_{j}"]
                    operators = [f"Op_{i}_{j}"]
                    h = compute_structure_hash(premises, operators)
                    writer.writerow({
                        'id': f'train_{i}_{j}',
                        'premises': ';'.join(premises),
                        'operators': ';'.join(operators),
                        'solution': f'Sol_{i}_{j}',
                        'entropy_level': 'mock',
                        'structure_hash': h,
                        'set_type': 'training',
                        'metadata': '{}'
                    })
    
    def teardown_method(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir)
    
    def test_load_existing_hashes(self):
        """Test that load_existing_hashes correctly reads hashes from CSVs."""
        hashes = load_existing_hashes(self.training_files)
        assert len(hashes) == 15  # 3 files * 5 samples each
        
        # Verify a specific hash is present
        sample_premises = ["P0_0"]
        sample_operators = ["Op_0_0"]
        expected_hash = compute_structure_hash(sample_premises, sample_operators)
        assert expected_hash in hashes
    
    def test_generate_unique_problem_excludes_existing(self):
        """Test that generate_unique_problem does not return problems with existing hashes."""
        existing_hashes = load_existing_hashes(self.training_files)
        
        # Generate a problem
        prob = generate_unique_problem(existing_hashes, max_attempts=100)
        
        assert prob is not None
        h = compute_structure_hash(prob.premises, prob.operators)
        assert h not in existing_hashes
    
    def test_generate_unique_problem_avoids_duplicates(self):
        """Test that generate_unique_problem avoids duplicates within its own generation."""
        existing_hashes = load_existing_hashes(self.training_files)
        generated_hashes = set()
        
        for _ in range(10):
            prob = generate_unique_problem(existing_hashes, max_attempts=100)
            assert prob is not None
            h = compute_structure_hash(prob.premises, prob.operators)
            assert h not in generated_hashes
            generated_hashes.add(h)
            # Add to existing set to force next one to be different
            existing_hashes.add(h)
    
    def test_write_test_set_csv_creates_file(self):
        """Test that write_test_set_csv creates the output file with correct headers."""
        mock_problems = [
            SyntheticProblem(
                id=f"test_{i}",
                premises=[f"P{i}"],
                operators=[f"Op{i}"],
                solution=f"S{i}",
                entropy_level="High",
                metadata={}
            ) for i in range(10)
        ]
        
        output_path = os.path.join(self.output_dir, "test_set.csv")
        write_test_set_csv(mock_problems, output_path, ["High"])
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 10
            assert all(row['set_type'] == 'test_generalization' for row in rows)
            assert 'structure_hash' in rows[0]
    
    def test_stratification_by_entropy(self):
        """Test that the output CSV contains stratified entropy levels."""
        # This is a simplified check; full logic is in main()
        mock_problems = [
            SyntheticProblem(
                id=f"test_{i}",
                premises=[f"P{i}"],
                operators=[f"Op{i}"],
                solution=f"S{i}",
                entropy_level="High" if i < 5 else "Low",
                metadata={'target_entropy': "High" if i < 5 else "Low"}
            ) for i in range(10)
        ]
        
        output_path = os.path.join(self.output_dir, "test_set.csv")
        write_test_set_csv(mock_problems, output_path, ["High", "Low"])
        
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            high_count = sum(1 for r in rows if r['entropy_level'] == 'High')
            low_count = sum(1 for r in rows if r['entropy_level'] == 'Low')
            
            assert high_count == 5
            assert low_count == 5
    
    def test_minimum_sample_count(self):
        """Verify that we can generate at least 500 samples without collision."""
        # Create a small training set to simulate real conditions
        existing_hashes = load_existing_hashes(self.training_files)
        
        count = 0
        max_attempts = 50000
        while count < 500 and count < max_attempts:
            prob = generate_unique_problem(existing_hashes, max_attempts=100)
            if prob:
                h = compute_structure_hash(prob.premises, prob.operators)
                existing_hashes.add(h)
                count += 1
        
        assert count >= 500, f"Failed to generate 500 unique samples. Got {count}."