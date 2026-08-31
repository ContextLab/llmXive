"""
Unit tests for stratified sampler functionality.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.sampler import stratified_sampler, save_sample_metadata
from code.utils.exceptions import DataValidationError


class TestStratifiedSampler:
    """Tests for the stratified_sampler function."""

    def setup_method(self):
        """Setup test fixtures."""
        np.random.seed(42)
        
        # Create synthetic M4-like data
        self.m4_data = pd.DataFrame({
            'series_id': [f'M4_{i}' for i in range(100)],
            'frequency': np.random.choice(['Yearly', 'Quarterly', 'Monthly'], 100)
        })
        
        # Create synthetic UCI-like data
        self.uci_data = pd.DataFrame({
            'series_id': [f'UCI_{i}' for i in range(100)],
            'mean_load': np.random.uniform(100, 1000, 100)
        })

    def test_m4_sampling_basic(self):
        """Test basic M4 stratified sampling."""
        sample = stratified_sampler(
            self.m4_data, 
            dataset_type='M4', 
            n_samples=20, 
            random_state=42
        )
        
        assert len(sample['series_id'].unique()) == 20
        assert set(sample['series_id']).issubset(set(self.m4_data['series_id']))

    def test_uci_sampling_basic(self):
        """Test basic UCI stratified sampling."""
        sample = stratified_sampler(
            self.uci_data, 
            dataset_type='UCI', 
            n_samples=30, 
            random_state=42
        )
        
        assert len(sample['series_id'].unique()) == 30
        assert set(sample['series_id']).issubset(set(self.uci_data['series_id']))

    def test_strata_representation_m4(self):
        """Test that M4 sampling preserves strata proportions."""
        # Create balanced strata
        balanced_data = pd.DataFrame({
            'series_id': [f'M4_{i}' for i in range(90)],
            'frequency': ['Yearly'] * 30 + ['Quarterly'] * 30 + ['Monthly'] * 30
        })
        
        sample = stratified_sampler(
            balanced_data, 
            dataset_type='M4', 
            n_samples=30, 
            random_state=42
        )
        
        strata_counts = sample['frequency'].value_counts()
        # Should be roughly equal (10 each)
        assert all(count >= 8 for count in strata_counts.values), "Strata not balanced"

    def test_strata_representation_uci(self):
        """Test that UCI sampling preserves strata proportions."""
        # Create balanced strata by manually assigning
        balanced_data = pd.DataFrame({
            'series_id': [f'UCI_{i}' for i in range(90)],
            'mean_load': (
                [100] * 30 +  # Low
                [500] * 30 +  # Medium
                [900] * 30    # High
            )
        })
        
        sample = stratified_sampler(
            balanced_data, 
            dataset_type='UCI', 
            n_samples=30, 
            random_state=42
        )
        
        # Calculate strata again
        q_low = sample['mean_load'].quantile(0.33)
        q_high = sample['mean_load'].quantile(0.66)
        
        def categorize(x):
            if x <= q_low: return 'Low'
            elif x <= q_high: return 'Medium'
            else: return 'High'
        
        sample['strata'] = sample['mean_load'].apply(categorize)
        strata_counts = sample['strata'].value_counts()
        
        assert all(count >= 8 for count in strata_counts.values), "Strata not balanced"

    def test_invalid_dataset_type(self):
        """Test error on invalid dataset type."""
        with pytest.raises(ValueError, match="dataset_type must be 'M4' or 'UCI'"):
            stratified_sampler(self.m4_data, dataset_type='Invalid', n_samples=10)

    def test_missing_series_id(self):
        """Test error when series_id is missing."""
        bad_data = self.m4_data.drop(columns=['series_id'])
        with pytest.raises(ValueError, match="must contain 'series_id' column"):
            stratified_sampler(bad_data, dataset_type='M4', n_samples=10)

    def test_missing_frequency_m4(self):
        """Test error when frequency is missing for M4."""
        bad_data = self.m4_data.drop(columns=['frequency'])
        with pytest.raises(ValueError, match="M4 data must contain a 'frequency' column"):
            stratified_sampler(bad_data, dataset_type='M4', n_samples=10)

    def test_missing_mean_load_uci(self):
        """Test error when mean_load is missing for UCI."""
        bad_data = self.uci_data.drop(columns=['mean_load'])
        with pytest.raises(ValueError, match="UCI data must contain a 'mean_load' column"):
            stratified_sampler(bad_data, dataset_type='UCI', n_samples=10)

    def test_n_samples_exceeds_total(self):
        """Test error when n_samples > total series."""
        with pytest.raises(RuntimeError, match="Requested .* samples but only .* available"):
            stratified_sampler(self.m4_data, dataset_type='M4', n_samples=200)

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        sample1 = stratified_sampler(
            self.m4_data, dataset_type='M4', n_samples=20, random_state=123
        )
        sample2 = stratified_sampler(
            self.m4_data, dataset_type='M4', n_samples=20, random_state=123
        )
        
        assert set(sample1['series_id']) == set(sample2['series_id'])

    def test_custom_strata_column(self):
        """Test using a custom strata column."""
        custom_data = self.m4_data.copy()
        custom_data['custom_strata'] = np.random.choice(['A', 'B'], 100)
        
        sample = stratified_sampler(
            custom_data, 
            dataset_type='M4', 
            n_samples=20, 
            strata_column='custom_strata',
            random_state=42
        )
        
        assert len(sample['series_id'].unique()) == 20

class TestSaveSampleMetadata:
    """Tests for save_sample_metadata function."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = Path(__file__).parent / "temp_test_output"
        self.temp_dir.mkdir(exist_ok=True)
        
        self.m4_data = pd.DataFrame({
            'series_id': [f'M4_{i}' for i in range(30)],
            'frequency': np.random.choice(['Yearly', 'Quarterly', 'Monthly'], 30)
        })
        
        self.uci_data = pd.DataFrame({
            'series_id': [f'UCI_{i}' for i in range(30)],
            'mean_load': np.random.uniform(100, 1000, 30)
        })

    def test_save_m4_metadata(self):
        """Test saving M4 metadata."""
        path = save_sample_metadata(
            self.m4_data, 
            dataset_type='M4', 
            output_dir=self.temp_dir
        )
        
        assert path.exists()
        df = pd.read_csv(path)
        assert 'series_id' in df.columns
        assert 'frequency' in df.columns or 'strata' in df.columns

    def test_save_uci_metadata(self):
        """Test saving UCI metadata."""
        path = save_sample_metadata(
            self.uci_data, 
            dataset_type='UCI', 
            output_dir=self.temp_dir
        )
        
        assert path.exists()
        df = pd.read_csv(path)
        assert 'series_id' in df.columns
        assert 'strata' in df.columns

    def teardown_method(self):
        """Cleanup temp files."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)