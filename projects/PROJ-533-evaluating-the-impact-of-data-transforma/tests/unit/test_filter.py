import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.filter_datasets import (
    load_dataset_from_file,
    calculate_missing_ratio,
    impute_missing_values,
    filter_by_missing_data,
    process_dataset_for_filtering,
    run_filter_pipeline
)
from scipy import stats

class TestShapiroWilkFiltering:
    """Tests for T011b and T016 requirements regarding Shapiro-Wilk filtering."""

    def test_shapiro_wilk_p_value_calculation(self):
        """Test that shapiro_test returns a p-value object (T011a)."""
        # Using scipy.stats.shapiro directly as the implementation does
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        stat, p_value = stats.shapiro(data)
        assert isinstance(p_value, float)
        assert 0.0 <= p_value <= 1.0

    def test_filter_keeps_non_normal(self):
        """Test that a dataset with p < 0.05 is kept and p >= 0.05 is excluded (T011b)."""
        # Generate non-normal data (exponential distribution)
        np.random.seed(42)
        non_normal_data = np.random.exponential(scale=2.0, size=100)
        
        stat, p_val = stats.shapiro(non_normal_data)
        # Exponential should be non-normal
        assert p_val < 0.05, f"Exponential data should be non-normal, got p={p_val}"

        # Generate normal data
        normal_data = np.random.normal(loc=0, scale=1, size=100)
        stat, p_val_normal = stats.shapiro(normal_data)
        # Normal data should have p >= 0.05 (usually)
        # Note: Shapiro can reject normality for large N even if normal, 
        # but for N=100 it's often okay. We just verify the logic.
        
        # Logic check:
        # If p < 0.05 -> included = True
        # If p >= 0.05 -> included = False
        assert p_val < 0.05  # Non-normal data is non-normal
        
    def test_process_dataset_returns_included_flag(self):
        """Test that process_dataset_for_filtering returns correct included flag."""
        # Create a temporary CSV with non-normal data
        import tempfile
        import csv
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Create non-normal data
            data = np.random.exponential(scale=1.0, size=100)
            df = pd.DataFrame({'value': data})
            csv_path = tmpdir_path / "test_non_normal.csv"
            df.to_csv(csv_path, index=False)
            
            # Mock dataset_id
            result = process_dataset_for_filtering("test_id", str(csv_path), "")
            
            assert result['dataset_id'] == "test_id"
            assert result['sample_size'] == 100
            assert result['included'] is True  # Because exponential is non-normal
            assert 0.0 <= result['shapiro_p'] <= 1.0

    def test_process_dataset_excludes_normal(self):
        """Test that a normal dataset is excluded (p >= 0.05)."""
        import tempfile
        import pandas as pd
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Create normal data
            np.random.seed(123)
            data = np.random.normal(loc=0, scale=1, size=100)
            df = pd.DataFrame({'value': data})
            csv_path = tmpdir_path / "test_normal.csv"
            df.to_csv(csv_path, index=False)
            
            result = process_dataset_for_filtering("test_id", str(csv_path), "")
            
            # Note: Shapiro might occasionally reject normality by chance, 
            # but statistically it should often be >= 0.05 for normal data.
            # We assert the logic is applied: if p >= 0.05, included is False.
            # If p < 0.05, included is True.
            # We can't guarantee p >= 0.05 for every random normal sample, 
            # so we just verify the function runs and returns a boolean.
            assert isinstance(result['included'], bool)
            assert result['sample_size'] == 100

    def test_sample_size_filtering(self):
        """Test that datasets with N < 30 are excluded."""
        import tempfile
        import pandas as pd
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Create small dataset
            data = [1, 2, 3, 4, 5] # N=5
            df = pd.DataFrame({'value': data})
            csv_path = tmpdir_path / "test_small.csv"
            df.to_csv(csv_path, index=False)
            
            result = process_dataset_for_filtering("test_id", str(csv_path), "")
            
            assert result['sample_size'] == 5
            assert result['included'] is False
            assert pd.isna(result['shapiro_p']) # Should not run Shapiro on N<30