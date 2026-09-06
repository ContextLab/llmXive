"""
Unit tests for aggregate_robustness.py (T026)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import pytest
import tempfile
import os

# We will mock the config manager to return temp paths
# Since we cannot easily import the real config without full project setup in a unit test context
# we will test the extraction logic directly by creating mock dataframes.

from aggregate_robustness import (
    extract_bootstrap_metrics,
    extract_alpha_sweep_metrics,
    extract_covariate_metrics,
    extract_binary_model_metrics,
    load_csv_safely
)


class TestExtractBootstrapMetrics:
    def test_extract_from_valid_df(self):
        data = {
            'interaction_coef': [0.5],
            'interaction_ci_lower': [0.1],
            'interaction_ci_upper': [0.9],
            'interaction_p_val': [0.03],
            'interaction_se': [0.2]
        }
        df = pd.DataFrame(data)
        metrics = extract_bootstrap_metrics(df)

        assert metrics['bootstrap_interaction_coef'] == 0.5
        assert metrics['bootstrap_ci_lower'] == 0.1
        assert metrics['bootstrap_ci_upper'] == 0.9
        assert metrics['bootstrap_se'] == 0.2
        assert metrics['bootstrap_significant'] is True

    def test_extract_from_none(self):
        metrics = extract_bootstrap_metrics(None)
        assert metrics['bootstrap_interaction_coef'] is None
        assert metrics['bootstrap_significant'] is None

    def test_extract_from_empty_df(self):
        df = pd.DataFrame()
        metrics = extract_bootstrap_metrics(df)
        assert metrics['bootstrap_interaction_coef'] is None


class TestExtractAlphaSweepMetrics:
    def test_extract_various_alphas(self):
        data = {
            'alpha_level': [0.01, 0.05, 0.10],
            'significant': [False, True, True]
        }
        df = pd.DataFrame(data)
        metrics = extract_alpha_sweep_metrics(df)

        assert metrics['alpha_sweep_001_significant'] is False
        assert metrics['alpha_sweep_005_significant'] is True
        assert metrics['alpha_sweep_010_significant'] is True

    def test_extract_missing_alpha(self):
        data = {
            'alpha_level': [0.05],
            'significant': [True]
        }
        df = pd.DataFrame(data)
        metrics = extract_alpha_sweep_metrics(df)

        assert metrics['alpha_sweep_001_significant'] is None
        assert metrics['alpha_sweep_005_significant'] is True
        assert metrics['alpha_sweep_010_significant'] is None


class TestExtractCovariateMetrics:
    def test_extract_basic(self):
        data = {
            'interaction_coef': [0.4],
            'interaction_p_val': [0.04]
        }
        df = pd.DataFrame(data)
        metrics = extract_covariate_metrics(df)

        assert metrics['covariate_interaction_coef'] == 0.4
        assert metrics['covariate_interaction_p_val'] == 0.04


class TestExtractBinaryModelMetrics:
    def test_extract_basic(self):
        data = {
            'interaction_coef': [0.3],
            'interaction_p_val': [0.06]
        }
        df = pd.DataFrame(data)
        metrics = extract_binary_model_metrics(df)

        assert metrics['binary_interaction_coef'] == 0.3
        assert metrics['binary_interaction_p_val'] == 0.06


class TestLoadCsvSafely:
    def test_load_existing_file(self, tmp_path):
        file_path = tmp_path / "test.csv"
        file_path.write_text("a,b\n1,2")
        df = load_csv_safely(file_path, "Test")
        assert df is not None
        assert df.shape == (1, 2)

    def test_load_missing_file(self, tmp_path):
        file_path = tmp_path / "nonexistent.csv"
        df = load_csv_safely(file_path, "Test")
        assert df is None
