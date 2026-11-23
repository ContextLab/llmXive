import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import pytest
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.run_simulation import (
    load_sensitivity_data,
    load_contaminated_datasets,
    run_single_test_iteration,
    run_monte_carlo_simulation,
    run_all_simulations,
    save_results
)
from code.utils.config import get_seed

class TestSimulationPipeline:
    """Integration tests for the simulation pipeline."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for test artifacts."""
        temp_base = Path(tempfile.mkdtemp())
        processed_dir = temp_base / "processed"
        results_dir = temp_base / "results"
        processed_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        yield processed_dir, results_dir
        # Cleanup
        shutil.rmtree(temp_base)

    @pytest.fixture
    def sample_sensitivity_data(self, temp_dirs):
        """Create a sample sensitivity.csv file."""
        processed_dir, _ = temp_dirs
        sensitivity_df = pd.DataFrame({
            'threshold': [1.0, 2.0, 3.0],
            'false_positive_rate': [0.05, 0.06, 0.08],
            'variation_in_fpr': [0.01, 0.02, 0.03]
        })
        sensitivity_path = processed_dir / "sensitivity.csv"
        sensitivity_df.to_csv(sensitivity_path, index=False)
        return sensitivity_path

    @pytest.fixture
    def sample_contaminated_data(self, temp_dirs):
        """Create sample contaminated dataset files."""
        processed_dir, _ = temp_dirs
        
        # Create two sample datasets
        np.random.seed(get_seed())
        
        # Dataset 1: Wine-like (clean-ish)
        data1 = pd.DataFrame({
            'col1': np.random.normal(0, 1, 1000),
            'col2': np.random.normal(0, 1, 1000)
        })
        file1 = processed_dir / "contaminated_wine_0.05.csv"
        data1.to_csv(file1, index=False)
        
        # Dataset 2: HAR-like (with some outliers)
        data2 = pd.DataFrame({
            'col1': np.random.normal(0, 1, 500),
            'col2': np.random.normal(0, 1, 500)
        })
        # Add some outliers
        data2.loc[:10, 'col1'] = 10.0
        file2 = processed_dir / "contaminated_har_0.10.csv"
        data2.to_csv(file2, index=False)
        
        return processed_dir

    def test_load_sensitivity_data(self, sample_sensitivity_data):
        """Test loading sensitivity data."""
        df = load_sensitivity_data(sample_sensitivity_data)
        assert 'threshold' in df.columns
        assert 'false_positive_rate' in df.columns
        assert 'variation_in_fpr' in df.columns
        assert len(df) == 3

    def test_load_contaminated_datasets(self, sample_contaminated_data):
        """Test loading contaminated datasets."""
        datasets = load_contaminated_datasets(sample_contaminated_data)
        assert len(datasets) == 2
        
        # Check structure
        for ds in datasets:
            assert 'dataset_name' in ds
            assert 'rate' in ds
            assert 'data' in ds
            assert isinstance(ds['data'], pd.DataFrame)
        
        # Check specific values
        rates = [ds['rate'] for ds in datasets]
        assert 0.05 in rates
        assert 0.10 in rates

    def test_run_single_test_iteration_clean_data(self, temp_dirs):
        """Test single iteration on clean data (should have ~5% rejection rate)."""
        processed_dir, _ = temp_dirs
        
        # Create clean data
        np.random.seed(get_seed())
        clean_data = pd.DataFrame({
            'col1': np.random.normal(0, 1, 1000),
            'col2': np.random.normal(0, 1, 1000)
        })
        
        # Run multiple iterations to estimate Type I error
        n_iter = 100
        rejections = 0
        
        for _ in range(n_iter):
            rejected, _ = run_single_test_iteration(
                clean_data, 
                contamination_rate=0.0, 
                magnitude=1.0
            )
            if rejected:
                rejections += 1
        
        error_rate = rejections / n_iter
        # With alpha=0.05, we expect error rate between 0.01 and 0.10 (statistical variance)
        assert 0.01 <= error_rate <= 0.10, f"Type I error rate {error_rate} is outside expected range"

    def test_run_monte_carlo_simulation_structure(self, sample_contaminated_data, sample_sensitivity_data):
        """Test Monte Carlo simulation returns correct structure."""
        datasets = load_contaminated_datasets(sample_contaminated_data)
        sensitivity_df = load_sensitivity_data(sample_sensitivity_data)
        
        # Run simulation for first dataset with first magnitude
        ds = datasets[0]
        result = run_monte_carlo_simulation(
            dataset_name=ds['dataset_name'],
            contamination_rate=ds['rate'],
            magnitude=sensitivity_df['threshold'].iloc[0],
            data=ds['data'],
            n_iterations=50, # Small for testing
            test_type="ttest"
        )
        
        assert 'dataset' in result
        assert 'rate' in result
        assert 'magnitude' in result
        assert 'error_rate' in result
        assert 'power' in result
        assert 0.0 <= result['error_rate'] <= 1.0
        assert 0.0 <= result['power'] <= 1.0

    def test_seed_reproducibility(self, temp_dirs):
        """Test that results are reproducible with the same seed."""
        processed_dir, _ = temp_dirs
        
        # Create data
        np.random.seed(get_seed())
        data = pd.DataFrame({
            'col1': np.random.normal(0, 1, 500),
            'col2': np.random.normal(0, 1, 500)
        })
        
        # Run simulation twice
        result1 = run_monte_carlo_simulation(
            dataset_name="test",
            contamination_rate=0.0,
            magnitude=1.0,
            data=data,
            n_iterations=20,
            test_type="ttest"
        )
        
        result2 = run_monte_carlo_simulation(
            dataset_name="test",
            contamination_rate=0.0,
            magnitude=1.0,
            data=data,
            n_iterations=20,
            test_type="ttest"
        )
        
        # Results should be identical due to fixed seed
        assert result1['error_rate'] == result2['error_rate']
        assert result1['power'] == result2['power']

    def test_save_results(self, temp_dirs):
        """Test saving results to CSV."""
        _, results_dir = temp_dirs
        
        results_df = pd.DataFrame({
            'dataset': ['test1', 'test2'],
            'rate': [0.05, 0.10],
            'magnitude': [1.0, 2.0],
            'error_rate': [0.05, 0.06],
            'power': [0.95, 0.94]
        })
        
        output_path = results_dir / "test_results.csv"
        save_results(results_df, output_path)
        
        assert output_path.exists()
        
        # Verify content
        loaded = pd.read_csv(output_path)
        assert len(loaded) == 2
        assert 'error_rate' in loaded.columns
        assert 'power' in loaded.columns
