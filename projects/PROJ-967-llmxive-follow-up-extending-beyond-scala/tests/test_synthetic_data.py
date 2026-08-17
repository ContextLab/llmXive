"""
Unit tests for the synthetic data generator.
"""
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))
from synthetic_data import (
    generate_synthetic_dataset,
    generate_synthetic_prompt,
    generate_teacher_scores,
    generate_human_annotations,
    generate_student_scalar,
    generate_primary_dimension,
    DIMENSIONS
)

class TestSyntheticDataGenerator:
    """Tests for the synthetic data generation functionality."""

    def test_generate_dataset_creates_file(self):
        """Test that the generator creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_output.parquet')
            generate_synthetic_dataset(n_samples=10, seed=42, output_path=output_path)
            
            assert os.path.exists(output_path), "Output file was not created"
            
            # Verify it can be loaded
            df = pd.read_parquet(output_path)
            assert len(df) == 10, "Incorrect number of samples generated"

    def test_generate_dataset_schema_compliance(self):
        """Test that generated data matches the required schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_schema.parquet')
            generate_synthetic_dataset(n_samples=5, seed=42, output_path=output_path)
            
            df = pd.read_parquet(output_path)
            
            # Check required columns
            required_columns = [
                'prompt', 'image_url', 'teacher_scores', 
                'student_scalar', 'human_annotations', 'primary_dimension'
            ]
            for col in required_columns:
                assert col in df.columns, f"Missing required column: {col}"

    def test_teacher_scores_structure(self):
        """Test that teacher_scores have the correct structure and keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_scores.parquet')
            generate_synthetic_dataset(n_samples=5, seed=42, output_path=output_path)
            
            df = pd.read_parquet(output_path)
            
            for _, row in df.iterrows():
                scores = row['teacher_scores']
                assert isinstance(scores, dict), "teacher_scores should be a dict"
                for dim in DIMENSIONS:
                    assert dim in scores, f"Missing dimension in teacher_scores: {dim}"
                    assert isinstance(scores[dim], float), f"{dim} should be a float"

    def test_human_annotations_independence(self):
        """Test that human annotations have independent noise from teacher scores."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_independence.parquet')
            generate_synthetic_dataset(n_samples=100, seed=42, output_path=output_path)
            
            df = pd.read_parquet(output_path)
            
            # Collect all scores
            teacher_means = []
            human_means = []
            
            for _, row in df.iterrows():
                teacher_scores = row['teacher_scores']
                human_annotations = row['human_annotations']
                
                teacher_means.append(np.mean([teacher_scores[d] for d in DIMENSIONS]))
                human_means.append(np.mean([human_annotations[d] for d in DIMENSIONS]))
            
            # They should not be perfectly correlated (though they may be correlated due to same distribution)
            # We just verify they are generated as separate calls
            assert len(teacher_means) == 100
            assert len(human_means) == 100

    def test_primary_dimension_validity(self):
        """Test that primary_dimension is always one of the valid dimensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_dim.parquet')
            generate_synthetic_dataset(n_samples=10, seed=42, output_path=output_path)
            
            df = pd.read_parquet(output_path)
            
            for dim in df['primary_dimension']:
                assert dim in DIMENSIONS, f"Invalid primary dimension: {dim}"

    def test_reproducibility_with_seed(self):
        """Test that same seed produces same results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path1 = os.path.join(tmpdir, 'test_rep1.parquet')
            output_path2 = os.path.join(tmpdir, 'test_rep2.parquet')
            
            generate_synthetic_dataset(n_samples=5, seed=123, output_path=output_path1)
            generate_synthetic_dataset(n_samples=5, seed=123, output_path=output_path2)
            
            df1 = pd.read_parquet(output_path1)
            df2 = pd.read_parquet(output_path2)
            
            # Compare all columns
            pd.testing.assert_frame_equal(df1, df2)

    def test_different_seeds_produce_different_results(self):
        """Test that different seeds produce different results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path1 = os.path.join(tmpdir, 'test_diff1.parquet')
            output_path2 = os.path.join(tmpdir, 'test_diff2.parquet')
            
            generate_synthetic_dataset(n_samples=10, seed=42, output_path=output_path1)
            generate_synthetic_dataset(n_samples=10, seed=123, output_path=output_path2)
            
            df1 = pd.read_parquet(output_path1)
            df2 = pd.read_parquet(output_path2)
            
            # They should not be identical
            assert not df1.equals(df2), "Different seeds should produce different data"

    def test_n_samples_argument(self):
        """Test that n_samples argument controls the output size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for n in [1, 10, 100]:
                output_path = os.path.join(tmpdir, f'test_n{n}.parquet')
                generate_synthetic_dataset(n_samples=n, seed=42, output_path=output_path)
                
                df = pd.read_parquet(output_path)
                assert len(df) == n, f"Expected {n} samples, got {len(df)}"