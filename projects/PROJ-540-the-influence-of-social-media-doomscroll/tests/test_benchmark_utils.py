"""
Tests for benchmark_utils module.
Verifies the synthetic data generator produces valid data with correct schema.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.benchmark_utils import generate_synthetic_data, generate_with_missing_values


class TestBenchmarkUtils:
    """Test suite for benchmark data generation functions."""
    
    def test_generate_synthetic_data_shape(self):
        """Test that the generated data has the correct number of rows."""
        n_samples = 1000
        df = generate_synthetic_data(n=n_samples, seed=42)
        
        assert len(df) == n_samples, f"Expected {n_samples} rows, got {len(df)}"
    
    def test_generate_synthetic_data_columns(self):
        """Test that all required columns are present."""
        required_columns = [
            'news_exposure_freq',
            'anxiety_score',
            'baseline_anxiety',
            'age',
            'gender',
            'social_media_engagement'
        ]
        
        df = generate_synthetic_data(n=100, seed=42)
        
        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"
    
    def test_generate_synthetic_data_dtypes(self):
        """Test that columns have appropriate data types."""
        df = generate_synthetic_data(n=100, seed=42)
        
        assert df['news_exposure_freq'].dtype in ['int64', 'int32'], "news_exposure_freq should be integer"
        assert df['age'].dtype in ['int64', 'int32'], "age should be integer"
        assert df['anxiety_score'].dtype in ['float64', 'float32'], "anxiety_score should be float"
        assert df['baseline_anxiety'].dtype in ['float64', 'float32'], "baseline_anxiety should be float"
    
    def test_generate_synthetic_data_ranges(self):
        """Test that values are within expected ranges."""
        df = generate_synthetic_data(n=1000, seed=42)
        
        # news_exposure_freq should be 1-5
        assert df['news_exposure_freq'].min() >= 1, "news_exposure_freq min should be >= 1"
        assert df['news_exposure_freq'].max() <= 5, "news_exposure_freq max should be <= 5"
        
        # anxiety_score and baseline_anxiety should be 0-100
        assert df['anxiety_score'].min() >= 0, "anxiety_score min should be >= 0"
        assert df['anxiety_score'].max() <= 100, "anxiety_score max should be <= 100"
        assert df['baseline_anxiety'].min() >= 0, "baseline_anxiety min should be >= 0"
        assert df['baseline_anxiety'].max() <= 100, "baseline_anxiety max should be <= 100"
        
        # age should be 18-75
        assert df['age'].min() >= 18, "age min should be >= 18"
        assert df['age'].max() <= 75, "age max should be <= 75"
    
    def test_reproducibility(self):
        """Test that the same seed produces the same results."""
        df1 = generate_synthetic_data(n=100, seed=42)
        df2 = generate_synthetic_data(n=100, seed=42)
        
        pd.testing.assert_frame_equal(df1, df2, "Same seed should produce identical data")
    
    def test_different_seeds_produce_different_data(self):
        """Test that different seeds produce different results."""
        df1 = generate_synthetic_data(n=100, seed=42)
        df2 = generate_synthetic_data(n=100, seed=123)
        
        # They should not be identical (probability of being identical is extremely low)
        assert not df1.equals(df2), "Different seeds should produce different data"
    
    def test_generate_with_missing_values(self):
        """Test that missing values are introduced correctly."""
        df = generate_with_missing_values(n=1000, seed=42, missing_rate=0.1)
        
        # Check that some values are missing in the specified columns
        for col in ['news_exposure_freq', 'anxiety_score', 'baseline_anxiety']:
            missing_count = df[col].isna().sum()
            assert missing_count > 0, f"Expected missing values in {col}"
            assert missing_count <= 200, f"Too many missing values in {col} (expected ~100)"
    
    def test_invalid_n_raises_error(self):
        """Test that invalid n values raise ValueError."""
        with pytest.raises(ValueError):
            generate_synthetic_data(n=0, seed=42)
        
        with pytest.raises(ValueError):
            generate_synthetic_data(n=-1, seed=42)
    
    def test_invalid_seed_raises_error(self):
        """Test that negative seed raises ValueError."""
        with pytest.raises(ValueError):
            generate_synthetic_data(n=100, seed=-1)
    
    def test_output_path_creates_file(self, tmp_path):
        """Test that output_path parameter creates a file."""
        output_file = tmp_path / "test_output.csv"
        
        df = generate_synthetic_data(n=100, seed=42, output_path=str(output_file))
        
        assert output_file.exists(), "Output file should be created"
        
        # Verify the file can be read
        df_read = pd.read_csv(output_file)
        assert len(df_read) == 100, "Read file should have same number of rows"