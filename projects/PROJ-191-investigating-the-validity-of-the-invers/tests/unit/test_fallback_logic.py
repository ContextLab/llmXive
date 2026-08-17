"""
Unit tests for fallback logic module (T016).
Tests bootstrap detection and state flag writing.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

from data.fallback_logic import detect_independent_runs, bootstrap_resample_dataset, main
from data.state_manager import read_state


class TestDetectIndependentRuns:
    """Tests for run detection logic."""
    
    def test_detect_single_run(self, tmp_path):
        """Test detection of a single run."""
        # Create a simple dataset with one run
        df = pd.DataFrame({
            'run_id': ['run1'] * 10,
            'separation': np.linspace(0.1, 1.0, 10),
            'force': np.random.randn(10)
        })
        
        csv_path = tmp_path / "test_data.csv"
        df.to_csv(csv_path, index=False)
        
        n_runs = detect_independent_runs(csv_path)
        assert n_runs == 1
    
    def test_detect_multiple_runs(self, tmp_path):
        """Test detection of multiple runs."""
        # Create a dataset with multiple runs
        df = pd.DataFrame({
            'run_id': ['run1'] * 5 + ['run2'] * 5 + ['run3'] * 5,
            'separation': np.tile(np.linspace(0.1, 1.0, 5), 3),
            'force': np.random.randn(15)
        })
        
        csv_path = tmp_path / "test_data.csv"
        df.to_csv(csv_path, index=False)
        
        n_runs = detect_independent_runs(csv_path)
        assert n_runs == 3
    
    def test_no_file(self, tmp_path):
        """Test behavior when file doesn't exist."""
        n_runs = detect_independent_runs(tmp_path / "nonexistent.csv")
        assert n_runs == 0
    
    def test_no_run_column(self, tmp_path):
        """Test behavior when no run column is found."""
        df = pd.DataFrame({
            'separation': np.linspace(0.1, 1.0, 10),
            'force': np.random.randn(10)
        })
        
        csv_path = tmp_path / "test_data.csv"
        df.to_csv(csv_path, index=False)
        
        n_runs = detect_independent_runs(csv_path)
        # Should return 1 when no run column is found
        assert n_runs == 1


class TestBootstrapResample:
    """Tests for bootstrap resampling logic."""
    
    def test_bootstrap_sample_count(self):
        """Test that correct number of bootstrap samples are generated."""
        df = pd.DataFrame({
            'x': np.arange(10),
            'y': np.random.randn(10)
        })
        
        samples = bootstrap_resample_dataset(df, n_bootstrap=100, random_seed=42)
        assert len(samples) == 100
    
    def test_bootstrap_sample_size(self):
        """Test that each bootstrap sample has the same size as original."""
        df = pd.DataFrame({
            'x': np.arange(20),
            'y': np.random.randn(20)
        })
        
        samples = bootstrap_resample_dataset(df, n_bootstrap=10, random_seed=42)
        for sample in samples:
            assert len(sample) == len(df)
    
    def test_bootstrap_with_replacement(self):
        """Test that bootstrap uses sampling with replacement."""
        df = pd.DataFrame({
            'x': np.arange(5),
            'y': [100, 200, 300, 400, 500]
        })
        
        # With a small dataset and many samples, we should see duplicates
        samples = bootstrap_resample_dataset(df, n_bootstrap=1000, random_seed=42)
        
        # Check that at least some samples contain duplicate indices
        has_duplicates = False
        for sample in samples:
            if len(sample) != len(sample['x'].unique()):
                has_duplicates = True
                break
        
        assert has_duplicates, "Bootstrap should use sampling with replacement"
    
    def test_reproducibility(self):
        """Test that bootstrap is reproducible with seed."""
        df = pd.DataFrame({
            'x': np.arange(10),
            'y': np.random.randn(10)
        })
        
        samples1 = bootstrap_resample_dataset(df, n_bootstrap=5, random_seed=123)
        samples2 = bootstrap_resample_dataset(df, n_bootstrap=5, random_seed=123)
        
        for s1, s2 in zip(samples1, samples2):
            pd.testing.assert_frame_equal(s1, s2)


class TestMain:
    """Tests for the main function."""
    
    def test_main_writes_state_file(self, tmp_path):
        """Test that main writes the state file correctly."""
        # Create a mock harmonized data file
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        
        df = pd.DataFrame({
            'run_id': ['run1'] * 5 + ['run2'] * 5,
            'separation': np.tile(np.linspace(0.1, 1.0, 5), 2),
            'force': np.random.randn(10)
        })
        
        csv_path = data_dir / "harmonized_data.csv"
        df.to_csv(csv_path, index=False)
        
        # Mock the project root by changing directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run main
            result = main()
            
            # Check state file was created
            state_path = data_dir / "state.json"
            assert state_path.exists(), "State file should be created"
            
            # Check state content
            with open(state_path) as f:
                state = json.load(f)
            
            assert "USE_BOOTSTRAP" in state
            assert state["detected_runs"] == 2
            assert state["bootstrap_threshold"] == 3
            
            # Since we have 2 runs (< 3), USE_BOOTSTRAP should be True
            assert state["USE_BOOTSTRAP"] == True
            assert result == True
            
        finally:
            os.chdir(original_cwd)
    
    def test_main_with_insufficient_runs(self, tmp_path):
        """Test main with fewer than 3 runs."""
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        
        df = pd.DataFrame({
            'run_id': ['run1'] * 10,
            'separation': np.linspace(0.1, 1.0, 10),
            'force': np.random.randn(10)
        })
        
        csv_path = data_dir / "harmonized_data.csv"
        df.to_csv(csv_path, index=False)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = main()
            
            state_path = data_dir / "state.json"
            with open(state_path) as f:
                state = json.load(f)
            
            assert state["USE_BOOTSTRAP"] == True
            assert result == True
            
        finally:
            os.chdir(original_cwd)
    
    def test_main_with_sufficient_runs(self, tmp_path):
        """Test main with 3 or more runs."""
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        
        df = pd.DataFrame({
            'run_id': ['run1'] * 5 + ['run2'] * 5 + ['run3'] * 5,
            'separation': np.tile(np.linspace(0.1, 1.0, 5), 3),
            'force': np.random.randn(15)
        })
        
        csv_path = data_dir / "harmonized_data.csv"
        df.to_csv(csv_path, index=False)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = main()
            
            state_path = data_dir / "state.json"
            with open(state_path) as f:
                state = json.load(f)
            
            assert state["USE_BOOTSTRAP"] == False
            assert result == False
            
        finally:
            os.chdir(original_cwd)