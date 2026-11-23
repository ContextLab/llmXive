"""
Unit tests for code/simulations.py
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from simulations import parse_args, load_data, prepare_model_data, fit_model, run_simulation

class TestSimulations:
    @pytest.fixture
    def sample_data(self):
        """Create a small synthetic dataset for testing."""
        np.random.seed(42)
        n = 100
        data = {
            'response_time': np.random.normal(1000, 200, n),
            'temperature_celsius': np.random.normal(20, 5, n),
            'participant_id': ['p' + str(i % 10) for i in range(n)],
            'dilemma_complexity': np.random.choice([1, 2, 3], n),
            'time_of_day': np.random.choice(['morning', 'afternoon', 'evening'], n)
        }
        return pd.DataFrame(data)

    def test_parse_args_default(self):
        args = parse_args()
        assert args.input == "data/processed/merged_dataset_with_covariates.parquet"
        assert args.output == "results/stats/individual_noise_simulation.json"
        assert args.n_iterations == 1000
        assert args.seed == 42

    def test_prepare_model_data(self, sample_data):
        df_clean, formula = prepare_model_data(sample_data)
        assert 'log_response_time' in df_clean.columns
        assert 'temperature_celsius' in formula
        assert 'participant_id' in df_clean.columns

    def test_fit_model(self, sample_data):
        df_clean, formula = prepare_model_data(sample_data)
        result = fit_model(df_clean, formula)
        assert result is not None
        assert 'temperature_celsius' in result.params

    def test_run_simulation(self, sample_data):
        df_clean, formula = prepare_model_data(sample_data)
        # Run a very small simulation for speed
        results = run_simulation(
            df_clean,
            formula,
            n_iterations=5,
            min_sd=100.0,
            max_sd=200.0,
            seed=42
        )
        assert len(results) > 0
        assert 'sd_baseline_noise_ms' in results[0]
        assert 'mean_temperature_coefficient_shift' in results[0]

    def test_integration_flow(self, sample_data):
        """Test the full flow from data preparation to simulation."""
        df_clean, formula = prepare_model_data(sample_data)
        results = run_simulation(df_clean, formula, n_iterations=3, min_sd=100, max_sd=100, seed=42)
        assert len(results) == 1 # Only one SD value in range
        assert results[0]['iterations_completed'] == 3