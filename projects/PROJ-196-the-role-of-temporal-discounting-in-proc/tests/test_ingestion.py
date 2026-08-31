import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from config import get_project_root, get_random_state
from ingestion import (
    hyperbolic_function,
    generate_delay_discounting_data,
    generate_procrastination_data,
    generate_nback_data,
    calculate_cronbach_alpha,
    fit_hyperbolic_model,
    harmonize_datasets,
    validate_core_constructs,
    write_harmonized_dataset
)

class TestHyperbolicFunction:
    def test_hyperbolic_basic(self):
        """Test basic hyperbolic function behavior"""
        result = hyperbolic_function(t=10, k=0.1)
        expected = 1.0 / (1.0 + 0.1 * 10)
        assert abs(result - expected) < 1e-10
    
    def test_hyperbolic_zero_delay(self):
        """Test that discount is 1.0 at zero delay"""
        result = hyperbolic_function(t=0, k=0.5)
        assert abs(result - 1.0) < 1e-10
    
    def test_hyperbolic_high_k(self):
        """Test that high k leads to higher discounting"""
        result_low = hyperbolic_function(t=10, k=0.1)
        result_high = hyperbolic_function(t=10, k=0.5)
        assert result_high < result_low

class TestDataGeneration:
    def test_generate_delay_discounting_data(self):
        """Test delay discounting data generation"""
        n = 10
        seed = 42
        df = generate_delay_discounting_data(n, seed)
        
        assert len(df) == n * 5  # 5 delay points per participant
        assert 'participant_id' in df.columns
        assert 'delay_days' in df.columns
        assert 'indifference_point' in df.columns
        
        # Check participant IDs are unique
        unique_pids = df['participant_id'].nunique()
        assert unique_pids == n
    
    def test_generate_procrastination_data(self):
        """Test procrastination data generation"""
        n = 10
        seed = 42
        df = generate_procrastination_data(n, seed)
        
        assert len(df) == n
        assert 'participant_id' in df.columns
        
        # Check item columns exist
        item_cols = [col for col in df.columns if col.startswith('item_')]
        assert len(item_cols) == 10
        
        # Check item values are in range 1-5
        for col in item_cols:
            assert df[col].min() >= 1
            assert df[col].max() <= 5
    
    def test_generate_nback_data(self):
        """Test n-back data generation"""
        n = 10
        seed = 42
        df = generate_nback_data(n, seed)
        
        assert len(df) == n
        assert 'participant_id' in df.columns
        assert 'wm_accuracy_2back' in df.columns
        assert 'wm_accuracy_3back' in df.columns
        assert 'wm_rt_2back' in df.columns
        assert 'wm_rt_3back' in df.columns
        
        # Check accuracy is in range 0-1
        assert df['wm_accuracy_2back'].min() >= 0
        assert df['wm_accuracy_2back'].max() <= 1

class TestCronbachAlpha:
    def test_cronbach_alpha_calculation(self):
        """Test Cronbach's alpha calculation"""
        # Create synthetic data with known reliability
        np.random.seed(42)
        n_participants = 50
        n_items = 5
        
        # Generate correlated items
        base = np.random.normal(0, 1, n_participants)
        items = np.column_stack([base + np.random.normal(0, 0.5, n_participants) for _ in range(n_items)])
        
        df = pd.DataFrame(items, columns=[f'item_{i}' for i in range(1, n_items + 1)])
        
        alpha = calculate_cronbach_alpha(df, [f'item_{i}' for i in range(1, n_items + 1)])
        
        # Alpha should be reasonable (> 0.5 for correlated items)
        assert 0.5 < alpha < 1.0

class TestModelFitting:
    def test_fit_hyperbolic_model(self):
        """Test hyperbolic model fitting"""
        np.random.seed(42)
        
        # Generate synthetic data with known k
        true_k = 0.1
        delays = np.array([1, 7, 30, 90, 365])
        true_values = 100.0 / (1.0 + true_k * delays)
        
        # Add noise
        noise = np.random.normal(0, 2.0, size=len(delays))
        observed_values = true_values + noise
        
        fitted_k = fit_hyperbolic_model(delays, observed_values, 42)
        
        # Fitted k should be close to true k
        assert 0.05 < fitted_k < 0.2

class TestHarmonization:
    def test_harmonize_datasets(self):
        """Test dataset harmonization"""
        n = 10
        seed = 42
        
        delay_df = generate_delay_discounting_data(n, seed)
        procrastination_df = generate_procrastination_data(n, seed + 1)
        nback_df = generate_nback_data(n, seed + 2)
        
        merged = harmonize_datasets(delay_df, procrastination_df, nback_df)
        
        # Check all participant IDs present
        assert len(merged) == n
        
        # Check required columns exist
        assert 'participant_id' in merged.columns
        assert 'procrastination_score' in merged.columns
        assert 'wm_accuracy_2back' in merged.columns

class TestValidation:
    def test_validate_core_constructs_success(self):
        """Test validation passes with correct data"""
        df = pd.DataFrame({
            'participant_id': ['sub_001', 'sub_002'],
            'discount_rate_k': [0.1, 0.2],
            'procrastination_score': [3.5, 4.0],
            'wm_accuracy': [0.8, 0.7]
        })
        
        # Should not raise
        validate_core_constructs(df)
    
    def test_validate_core_constructs_missing(self):
        """Test validation fails with missing construct"""
        df = pd.DataFrame({
            'participant_id': ['sub_001', 'sub_002'],
            'discount_rate_k': [0.1, 0.2],
            'procrastination_score': [3.5, 4.0]
            # Missing wm_accuracy
        })
        
        with pytest.raises(SystemExit) as exc_info:
            validate_core_constructs(df)
        
        assert exc_info.value.code == 1

class TestWriteDataset:
    def test_write_harmonized_dataset(self, tmp_path):
        """Test writing harmonized dataset to parquet"""
        df = pd.DataFrame({
            'participant_id': ['sub_001', 'sub_002'],
            'discount_rate_k': [0.1, 0.2],
            'procrastination_score': [3.5, 4.0],
            'wm_accuracy': [0.8, 0.7]
        })
        
        output_path = tmp_path / 'test_dataset.parquet'
        write_harmonized_dataset(df, output_path)
        
        # Check file exists
        assert output_path.exists()
        
        # Check can read back
        read_df = pd.read_parquet(output_path)
        assert len(read_df) == 2
        assert 'discount_rate_k' in read_df.columns
