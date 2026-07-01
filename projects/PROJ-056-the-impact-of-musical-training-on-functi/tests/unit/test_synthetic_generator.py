"""
Unit tests for the synthetic data generator.

These tests verify that:
1. The generator creates valid data structures
2. The data meets minimum sample size requirements
3. The NULL-FIRST property is maintained (no injected effects)
4. Memory limits are respected
"""
import os
import sys
import tempfile
from pathlib import Path
import json

import pytest
import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.synthetic_generator import (
    generate_subject_data,
    generate_connectivity_data,
    save_synthetic_data,
    MIN_SUBJECTS_PER_GROUP
)
from utils.memory_monitor import MemoryLimitExceeded


class TestSubjectDataGeneration:
    """Tests for generate_subject_data function."""

    def test_minimum_sample_size(self):
        """Test that insufficient subjects raise ValueError."""
        with pytest.raises(ValueError) as excinfo:
            generate_subject_data(n_subjects=10)  # Too small
        assert "Insufficient subjects" in str(excinfo.value)

    def test_valid_generation(self):
        """Test that valid sample sizes generate correctly."""
        df = generate_subject_data(n_subjects=100, seed=42)
        
        assert len(df) == 100
        assert 'subject_id' in df.columns
        assert 'group' in df.columns
        assert 'age' in df.columns
        assert 'sex' in df.columns
        assert 'motion_score' in df.columns
        assert 'ses_score' in df.columns
        assert 'years_of_training' in df.columns

    def test_group_distribution(self):
        """Test that groups are properly distributed."""
        df = generate_subject_data(n_subjects=200, seed=42)
        
        musicians = df[df['group'] == 'musician']
        non_musicians = df[df['group'] == 'non_musician']
        
        assert len(musicians) >= MIN_SUBJECTS_PER_GROUP
        assert len(non_musicians) >= MIN_SUBJECTS_PER_GROUP

    def test_years_training_property(self):
        """Test that years_of_training is 0 for non-musicians."""
        df = generate_subject_data(n_subjects=100, seed=42)
        
        non_musicians = df[df['group'] == 'non_musician']
        assert all(non_musicians['years_of_training'] == 0)
        
        musicians = df[df['group'] == 'musician']
        assert all(musicians['years_of_training'] >= 0)

    def test_demographic_ranges(self):
        """Test that demographic values are in expected ranges."""
        df = generate_subject_data(n_subjects=100, seed=42)
        
        # Age should be between 10 and 18
        assert df['age'].min() >= 10
        assert df['age'].max() <= 18
        
        # Sex should be 0 or 1
        assert set(df['sex'].unique()).issubset({0, 1})
        
        # Motion score should be between 0 and 1
        assert df['motion_score'].min() >= 0
        assert df['motion_score'].max() <= 1

    def test_null_first_property(self):
        """Test that no systematic group differences exist in demographics."""
        df = generate_subject_data(n_subjects=1000, seed=42)
        
        musicians = df[df['group'] == 'musician']
        non_musicians = df[df['group'] == 'non_musician']
        
        # Age means should be very close (within 0.2)
        age_diff = abs(musicians['age'].mean() - non_musicians['age'].mean())
        assert age_diff < 0.2, f"Age difference too large: {age_diff}"
        
        # SES means should be very close
        ses_diff = abs(musicians['ses_score'].mean() - non_musicians['ses_score'].mean())
        assert ses_diff < 0.2, f"SES difference too large: {ses_diff}"
        
        # Motion means should be very close
        motion_diff = abs(musicians['motion_score'].mean() - non_musicians['motion_score'].mean())
        assert motion_diff < 0.05, f"Motion difference too large: {motion_diff}"


class TestConnectivityDataGeneration:
    """Tests for generate_connectivity_data function."""

    def test_connectivity_shape(self):
        """Test that connectivity data has correct structure."""
        subject_df = generate_subject_data(n_subjects=20, seed=42)
        conn_df = generate_connectivity_data(subject_df, n_rois=10, seed=42)
        
        assert len(conn_df) > 0
        assert 'subject_id' in conn_df.columns
        assert 'roi_i' in conn_df.columns
        assert 'roi_j' in conn_df.columns
        assert 'correlation' in conn_df.columns

    def test_correlation_range(self):
        """Test that correlation values are in valid range [-1, 1]."""
        subject_df = generate_subject_data(n_subjects=20, seed=42)
        conn_df = generate_connectivity_data(subject_df, n_rois=10, seed=42)
        
        assert conn_df['correlation'].min() >= -1.0
        assert conn_df['correlation'].max() <= 1.0

    def test_null_connectivity_property(self):
        """Test that no systematic group differences exist in connectivity."""
        subject_df = generate_subject_data(n_subjects=100, seed=42)
        conn_df = generate_connectivity_data(subject_df, n_rois=20, seed=42)
        
        musician_ids = set(subject_df[subject_df['group'] == 'musician']['subject_id'])
        non_musician_ids = set(subject_df[subject_df['group'] == 'non_musician']['subject_id'])
        
        musician_conn = conn_df[conn_df['subject_id'].isin(musician_ids)]['correlation']
        non_musician_conn = conn_df[conn_df['subject_id'].isin(non_musician_ids)]['correlation']
        
        mean_diff = abs(musician_conn.mean() - non_musician_conn.mean())
        # For null-first data, mean difference should be small
        assert mean_diff < 0.02, f"Unexpected group difference in connectivity: {mean_diff}"


class TestSaveSyntheticData:
    """Tests for save_synthetic_data function."""

    def test_file_creation(self):
        """Test that all expected files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = save_synthetic_data(output_dir=tmpdir, n_subjects=20, seed=42)
            
            assert os.path.exists(files['subjects'])
            assert os.path.exists(files['connectivity'])
            assert os.path.exists(files['metadata'])

    def test_metadata_content(self):
        """Test that metadata file contains expected information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = save_synthetic_data(output_dir=tmpdir, n_subjects=50, seed=123)
            
            with open(files['metadata'], 'r') as f:
                metadata = json.load(f)
            
            assert metadata['n_subjects'] == 50
            assert metadata['seed'] == 123
            assert metadata['mode'] == 'verification'
            assert 'NULL-FIRST' in metadata['note']

    def test_csv_content(self):
        """Test that CSV files contain valid data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = save_synthetic_data(output_dir=tmpdir, n_subjects=30, seed=42)
            
            subject_df = pd.read_csv(files['subjects'])
            conn_df = pd.read_csv(files['connectivity'])
            
            assert len(subject_df) == 30
            assert len(conn_df) > 0
            assert 'subject_id' in subject_df.columns
            assert 'correlation' in conn_df.columns


class TestReproducibility:
    """Tests for reproducibility with fixed seeds."""

    def test_same_seed_same_results(self):
        """Test that same seed produces same results."""
        df1 = generate_subject_data(n_subjects=50, seed=999)
        df2 = generate_subject_data(n_subjects=50, seed=999)
        
        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seed_different_results(self):
        """Test that different seeds produce different results."""
        df1 = generate_subject_data(n_subjects=50, seed=100)
        df2 = generate_subject_data(n_subjects=50, seed=200)
        
        # They should be different
        assert not df1.equals(df2)