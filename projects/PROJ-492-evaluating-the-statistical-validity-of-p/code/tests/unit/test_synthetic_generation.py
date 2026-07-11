"""
Unit tests for synthetic dataset generation (T026).
Verifies that the synthetic generator produces valid data with correct structure.
"""
import csv
import json
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import pytest
import numpy as np

from code.src.audit.synthetic import (
    set_all_seeds,
    generate_sample_sizes,
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_synthetic_dataset,
    verify_outcome_types,
    MIN_SAMPLE_SIZE,
    MAX_SAMPLE_SIZE
)
from code.src.config import SEED


class TestSyntheticGeneration:
    """Tests for synthetic dataset generation functionality."""

    def test_set_all_seeds_determinism(self):
        """Test that setting seeds produces deterministic results."""
        set_all_seeds(SEED)
        result1 = np.random.random(5)
        
        set_all_seeds(SEED)
        result2 = np.random.random(5)
        
        assert np.array_equal(result1, result2)

    def test_generate_sample_sizes_range(self):
        """Test that generated sample sizes are within expected range."""
        sample_sizes = generate_sample_sizes(100)
        
        for control_size, treatment_size in sample_sizes:
            assert MIN_SAMPLE_SIZE <= control_size <= MAX_SAMPLE_SIZE
            assert MIN_SAMPLE_SIZE <= treatment_size <= MAX_SAMPLE_SIZE

    def test_generate_binary_outcome_structure(self):
        """Test that binary outcome records have correct structure."""
        sample_sizes = generate_sample_sizes(10)
        records = generate_binary_outcome(10, sample_sizes)
        
        required_fields = [
            'outcome_type', 'control_sample_size', 'treatment_sample_size',
            'control_successes', 'treatment_successes', 'baseline_rate',
            'effect_size', 'p_value', 'ci_lower', 'ci_upper',
            'is_inconsistent', 'true_p_value'
        ]
        
        for record in records:
            assert record['outcome_type'] == 'binary'
            for field in required_fields:
                assert field in record
            
            # Verify logical constraints
            assert 0 <= record['control_successes'] <= record['control_sample_size']
            assert 0 <= record['treatment_successes'] <= record['treatment_sample_size']
            assert 0 <= record['baseline_rate'] <= 1
            assert 0 <= record['p_value'] <= 1

    def test_generate_continuous_outcome_structure(self):
        """Test that continuous outcome records have correct structure."""
        sample_sizes = generate_sample_sizes(10)
        records = generate_continuous_outcome(10, sample_sizes)
        
        required_fields = [
            'outcome_type', 'control_sample_size', 'treatment_sample_size',
            'control_mean', 'control_std', 'treatment_mean', 'treatment_std',
            'effect_size', 'p_value', 'ci_lower', 'ci_upper',
            'is_inconsistent', 'true_p_value'
        ]
        
        for record in records:
            assert record['outcome_type'] == 'continuous'
            for field in required_fields:
                assert field in record
            
            # Verify logical constraints
            assert record['control_std'] >= 0
            assert record['treatment_std'] >= 0
            assert 0 <= record['p_value'] <= 1

    def test_generate_synthetic_dataset_minimum_records(self):
        """Test that the generator creates at least 10,000 records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            synthetic_path, metadata_path = generate_synthetic_dataset(
                n_records=10000,
                output_dir=output_dir,
                seed=SEED
            )
            
            # Verify file exists
            assert synthetic_path.exists()
            
            # Count records
            with open(synthetic_path, 'r') as f:
                reader = csv.DictReader(f)
                record_count = sum(1 for _ in reader)
            
            assert record_count >= 10000

    def test_generate_synthetic_dataset_both_outcome_types(self):
        """Test that the dataset contains both binary and continuous outcomes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            synthetic_path, _ = generate_synthetic_dataset(
                n_records=10000,
                binary_ratio=0.5,
                output_dir=output_dir,
                seed=SEED
            )
            
            outcome_counts = {'binary': 0, 'continuous': 0}
            
            with open(synthetic_path, 'r') as f:
                reader = csv.DictReader(f)
                for record in reader:
                    outcome_type = record['outcome_type']
                    if outcome_type in outcome_counts:
                        outcome_counts[outcome_type] += 1
            
            # Verify both types are present
            assert outcome_counts['binary'] > 0
            assert outcome_counts['continuous'] > 0

    def test_generate_synthetic_dataset_metadata(self):
        """Test that metadata file is created with required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            _, metadata_path = generate_synthetic_dataset(
                n_records=10000,
                output_dir=output_dir,
                seed=SEED
            )
            
            assert metadata_path.exists()
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            required_fields = [
                'generated_at', 'seed', 'total_records',
                'binary_records', 'continuous_records', 'constraints'
            ]
            
            for field in required_fields:
                assert field in metadata

    def test_verify_outcome_types(self):
        """Test the outcome type verification function."""
        records = [
            {'outcome_type': 'binary'},
            {'outcome_type': 'continuous'},
            {'outcome_type': 'binary'},
            {'outcome_type': 'other'}
        ]
        
        counts = verify_outcome_types(records)
        
        assert counts['binary'] == 2
        assert counts['continuous'] == 1
        assert counts['other'] == 1

    def test_synthetic_data_constraints_preserved(self):
        """Test that generated data respects defined constraints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            synthetic_path, _ = generate_synthetic_dataset(
                n_records=10000,
                output_dir=output_dir,
                seed=SEED
            )
            
            with open(synthetic_path, 'r') as f:
                reader = csv.DictReader(f)
                for record in reader:
                    # Check sample size constraints
                    control_size = int(record['control_sample_size'])
                    treatment_size = int(record['treatment_sample_size'])
                    
                    assert MIN_SAMPLE_SIZE <= control_size <= MAX_SAMPLE_SIZE
                    assert MIN_SAMPLE_SIZE <= treatment_size <= MAX_SAMPLE_SIZE
                    
                    # Check p-value constraints
                    p_value = float(record['p_value'])
                    assert 0 <= p_value <= 1

    def test_synthetic_dataset_reproducibility(self):
        """Test that the same seed produces identical results."""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                output_dir1 = Path(tmpdir1)
                output_dir2 = Path(tmpdir2)
                
                synthetic_path1, _ = generate_synthetic_dataset(
                    n_records=100,
                    output_dir=output_dir1,
                    seed=SEED
                )
                
                synthetic_path2, _ = generate_synthetic_dataset(
                    n_records=100,
                    output_dir=output_dir2,
                    seed=SEED
                )
                
                # Read both files
                with open(synthetic_path1, 'r') as f1:
                    data1 = f1.read()
                with open(synthetic_path2, 'r') as f2:
                    data2 = f2.read()
                
                # Files should be identical
                assert data1 == data2

    def test_synthetic_dataset_inconsistency_markers(self):
        """Test that inconsistent records are properly marked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            synthetic_path, _ = generate_synthetic_dataset(
                n_records=1000,
                output_dir=output_dir,
                seed=SEED
            )
            
            inconsistent_count = 0
            consistent_count = 0
            
            with open(synthetic_path, 'r') as f:
                reader = csv.DictReader(f)
                for record in reader:
                    if record['is_inconsistent'] == 'True':
                        inconsistent_count += 1
                    else:
                        consistent_count += 1
            
            # Should have approximately 15% inconsistent records
            total = inconsistent_count + consistent_count
            inconsistency_rate = inconsistent_count / total
            
            # Allow some tolerance due to rounding
            assert 0.10 <= inconsistency_rate <= 0.20

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
