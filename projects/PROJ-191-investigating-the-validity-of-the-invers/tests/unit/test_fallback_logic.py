"""
Unit tests for the fallback logic module.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

from data.fallback_logic import (
    detect_independent_runs,
    check_and_set_bootstrap_flag,
    bootstrap_resample_dataset,
    prepare_analysis_dataset
)
from data.state_manager import read_state

class TestDetectIndependentRuns:
    def test_detect_runs_with_csv_files(self, tmp_path):
        """Test detection of independent runs with CSV files present."""
        # Create some CSV files
        (tmp_path / "run1.csv").touch()
        (tmp_path / "run2.csv").touch()
        (tmp_path / "run3.csv").touch()
        
        count = detect_independent_runs(tmp_path)
        assert count == 3
    
    def test_detect_runs_with_no_files(self, tmp_path):
        """Test detection when no CSV files are present."""
        count = detect_independent_runs(tmp_path)
        assert count == 0
    
    def test_detect_runs_with_nonexistent_directory(self):
        """Test detection when directory doesn't exist."""
        nonexistent = Path("/nonexistent/path/that/does/not/exist")
        count = detect_independent_runs(nonexistent)
        assert count == 0
    
    def test_detect_runs_ignores_non_csv_files(self, tmp_path):
        """Test that non-CSV files are ignored."""
        (tmp_path / "run1.csv").touch()
        (tmp_path / "run2.txt").touch()
        (tmp_path / "run3.json").touch()
        
        count = detect_independent_runs(tmp_path)
        assert count == 1

class TestCheckAndSetBootstrapFlag:
    def test_bootstrap_flag_set_when_few_runs(self, tmp_path):
        """Test that bootstrap flag is set when fewer than 3 runs."""
        state_path = tmp_path / "state.json"
        
        # Test with 2 runs (should trigger bootstrap)
        use_bootstrap = check_and_set_bootstrap_flag(2, state_path)
        
        assert use_bootstrap is True
        
        # Verify state was written correctly
        state = read_state(state_path)
        assert state['USE_BOOTSTRAP'] is True
        assert state['run_count'] == 2
        assert state['bootstrap_required'] is True
    
    def test_bootstrap_flag_not_set_when_sufficient_runs(self, tmp_path):
        """Test that bootstrap flag is not set when 3 or more runs."""
        state_path = tmp_path / "state.json"
        
        # Test with 3 runs (should not trigger bootstrap)
        use_bootstrap = check_and_set_bootstrap_flag(3, state_path)
        
        assert use_bootstrap is False
        
        # Verify state was written correctly
        state = read_state(state_path)
        assert state['USE_BOOTSTRAP'] is False
        assert state['run_count'] == 3
        assert state['bootstrap_required'] is False
    
    def test_bootstrap_flag_not_set_with_many_runs(self, tmp_path):
        """Test that bootstrap flag is not set with many runs."""
        state_path = tmp_path / "state.json"
        
        use_bootstrap = check_and_set_bootstrap_flag(10, state_path)
        
        assert use_bootstrap is False
        
        state = read_state(state_path)
        assert state['USE_BOOTSTRAP'] is False
        assert state['run_count'] == 10
    
    def test_updates_existing_state(self, tmp_path):
        """Test that existing state is updated correctly."""
        state_path = tmp_path / "state.json"
        
        # Create initial state
        initial_state = {
            'project': 'test',
            'version': '1.0',
            'existing_field': 'value'
        }
        with open(state_path, 'w') as f:
            json.dump(initial_state, f)
        
        # Update with run count check
        use_bootstrap = check_and_set_bootstrap_flag(1, state_path)
        
        # Verify state was updated but not overwritten
        state = read_state(state_path)
        assert state['project'] == 'test'
        assert state['version'] == '1.0'
        assert state['existing_field'] == 'value'
        assert state['USE_BOOTSTRAP'] is True
        assert state['run_count'] == 1

class TestBootstrapResampleDataset:
    def test_resample_same_size(self):
        """Test that resampling with same size returns correct length."""
        df = pd.DataFrame({'x': range(100), 'y': range(100, 200)})
        resampled = bootstrap_resample_dataset(df, n_samples=100, random_seed=42)
        
        assert len(resampled) == 100
        assert list(resampled.columns) == ['x', 'y']
    
    def test_resample_different_size(self):
        """Test that resampling with different size returns correct length."""
        df = pd.DataFrame({'x': range(100), 'y': range(100, 200)})
        resampled = bootstrap_resample_dataset(df, n_samples=50, random_seed=42)
        
        assert len(resampled) == 50
    
    def test_resample_with_replacement(self):
        """Test that resampling uses replacement (can have duplicates)."""
        df = pd.DataFrame({'x': range(10), 'y': range(10, 20)})
        # With small dataset and replacement, we expect some duplicates
        resampled = bootstrap_resample_dataset(df, n_samples=100, random_seed=42)
        
        assert len(resampled) == 100
        # Check that some values are repeated (due to replacement)
        assert len(resampled['x'].unique()) < 100
    
    def test_resample_preserves_data(self):
        """Test that resampled data contains only values from original."""
        df = pd.DataFrame({'x': [1, 2, 3, 4, 5], 'y': [10, 20, 30, 40, 50]})
        resampled = bootstrap_resample_dataset(df, n_samples=10, random_seed=42)
        
        # All x values should be in original x values
        assert all(x in [1, 2, 3, 4, 5] for x in resampled['x'])
        # All y values should be in original y values
        assert all(y in [10, 20, 30, 40, 50] for y in resampled['y'])
    
    def test_reproducibility_with_seed(self):
        """Test that same seed produces same result."""
        df = pd.DataFrame({'x': range(100), 'y': range(100, 200)})
        
        resampled1 = bootstrap_resample_dataset(df, n_samples=50, random_seed=123)
        resampled2 = bootstrap_resample_dataset(df, n_samples=50, random_seed=123)
        
        pd.testing.assert_frame_equal(resampled1, resampled2)

class TestPrepareAnalysisDataset:
    def test_prepare_without_bootstrap(self):
        """Test preparation without bootstrap resampling."""
        df = pd.DataFrame({'x': range(100), 'y': range(100, 200)})
        
        processed, metadata = prepare_analysis_dataset(df, use_bootstrap=False)
        
        assert len(processed) == 100
        assert metadata['original_size'] == 100
        assert metadata['use_bootstrap'] is False
        assert metadata['n_bootstrap_samples'] == 0
    
    def test_prepare_with_bootstrap(self):
        """Test preparation with bootstrap resampling enabled."""
        df = pd.DataFrame({'x': range(100), 'y': range(100, 200)})
        
        processed, metadata = prepare_analysis_dataset(
            df, 
            use_bootstrap=True, 
            n_bootstrap_samples=1000
        )
        
        # Original dataset is returned, but metadata indicates bootstrap mode
        assert len(processed) == 100
        assert metadata['original_size'] == 100
        assert metadata['use_bootstrap'] is True
        assert metadata['n_bootstrap_samples'] == 1000
        assert 'bootstrap_note' in metadata
    
    def test_prepare_with_custom_seed(self):
        """Test preparation with custom random seed."""
        df = pd.DataFrame({'x': range(100), 'y': range(100, 200)})
        
        processed, metadata = prepare_analysis_dataset(
            df, 
            use_bootstrap=True, 
            random_seed=456
        )
        
        assert metadata['original_size'] == 100
        assert metadata['use_bootstrap'] is True