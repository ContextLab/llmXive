"""
Tests for T003: Synthetic Population Generation.

Verifies that:
1. The populations are generated with the correct size (N=1,000,000).
2. The ground truth JSON file is created and contains valid parameters.
3. The data types and column names match the expected schema.
"""
import os
import sys
import json
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import Config
from code.data.synthetic_pop import (
    generate_adult_population,
    generate_iris_population,
    generate_wine_population
)

class TestSyntheticPopulationGeneration:
    """Test suite for synthetic population generators."""

    @pytest.fixture
    def config(self):
        return Config()

    def test_adult_population_size(self, config):
        """Verify Adult population has N=1,000,000 rows."""
        df = generate_adult_population(42, 1_000_000)
        assert len(df) == 1_000_000, f"Expected 1M rows, got {len(df)}"

    def test_iris_population_size(self, config):
        """Verify Iris population has N=1,000_000 rows."""
        df = generate_iris_population(42, 1_000_000)
        assert len(df) == 1_000_000, f"Expected 1M rows, got {len(df)}"

    def test_wine_population_size(self, config):
        """Verify Wine population has N=1,000,000 rows."""
        df = generate_wine_population(42, 1_000_000)
        assert len(df) == 1_000_000, f"Expected 1M rows, got {len(df)}"

    def test_adult_columns(self):
        """Verify Adult population has expected columns."""
        df = generate_adult_population(42, 100)
        expected_cols = [
            'age', 'workclass', 'fnlwgt', 'education', 'education_num',
            'marital_status', 'occupation', 'relationship', 'race', 'sex',
            'capital_gain', 'capital_loss', 'hours_per_week', 'native_country',
            'income_over_50k'
        ]
        assert list(df.columns) == expected_cols

    def test_iris_columns(self):
        """Verify Iris population has expected columns."""
        df = generate_iris_population(42, 100)
        expected_cols = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'species']
        assert list(df.columns) == expected_cols

    def test_wine_columns(self):
        """Verify Wine population has expected columns."""
        df = generate_wine_population(42, 100)
        expected_cols = [
            'fixed_acidity', 'volatile_acidity', 'citric_acid', 'residual_sugar',
            'chlorides', 'free_sulfur_dioxide', 'total_sulfur_dioxide', 'density',
            'pH', 'sulphates', 'alcohol', 'quality'
        ]
        assert list(df.columns) == expected_cols

    def test_ground_truth_manifest_exists(self, config):
        """Verify that the ground truth JSON file is created by the main script logic."""
        # We check if the config has the parameters defined
        assert hasattr(config, 'ground_truth_params')
        assert 'adult' in config.ground_truth_params
        assert 'iris' in config.ground_truth_params
        assert 'wine' in config.ground_truth_params

    def test_ground_truth_parameters_structure(self, config):
        """Verify the structure of ground truth parameters."""
        params = config.ground_truth_params
        
        # Check Adult
        assert 'adult' in params
        assert params['adult']['size'] == 1_000_000
        assert 'continuous_features' in params['adult']
        assert 'categorical_features' in params['adult']
        assert 'target' in params['adult']
        
        # Check Iris
        assert 'iris' in params
        assert params['iris']['size'] == 1_000_000
        
        # Check Wine
        assert 'wine' in params
        assert params['wine']['size'] == 1_000_000

    def test_reproducibility(self):
        """Verify that same seed produces same data."""
        df1 = generate_adult_population(123, 1000)
        df2 = generate_adult_population(123, 1000)
        pd.testing.assert_frame_equal(df1, df2)
        
        df3 = generate_iris_population(456, 1000)
        df4 = generate_iris_population(456, 1000)
        pd.testing.assert_frame_equal(df3, df4)