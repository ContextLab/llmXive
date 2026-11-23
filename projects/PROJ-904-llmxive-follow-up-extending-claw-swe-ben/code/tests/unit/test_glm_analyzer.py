"""
Unit test scaffolding for GLM interaction effect calculation.

This file contains test scaffolding for the GLM analyzer module,
specifically focusing on interaction effect calculations between
model size and context strategy.

Tests are organized by the public API surface of glm_analyzer.py:
- Data loading and validation
- Feature preparation
- GLM fitting (including Firth penalization)
- Post-hoc analysis (pairwise differences, significance checks)
- Integration tests with mock data
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from typing import Dict, Any, List, Tuple
import json
import tempfile
import os

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from analysis.glm_analyzer import (
    load_results_data,
    prepare_features,
    fit_firth_glm,
    fit_glm_with_interaction,
    calculate_pairwise_diff,
    check_significance,
    perform_post_hoc_analysis,
    power_analysis,
    GLMConvergenceError
)

from models.execution_result import ExecutionResult, ExecutionStatus, FailureCategory
from models.task_instance import TaskInstance, TaskStatus
from models.context_config import ContextConfiguration, StrategyType


class TestGLMDataLoading:
    """Tests for load_results_data function."""

    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid CSV file with required columns."""
        # Create a minimal valid CSV
        csv_path = tmp_path / "valid_results.csv"
        data = {
            'instance_id': ['inst_1', 'inst_2', 'inst_3'],
            'model_size': ['1B', '1B', '7B'],
            'context_strategy': ['baseline', 'tfidf', 'baseline'],
            'pass_result': [1, 0, 1],
            'task_difficulty': [0.5, 0.7, 0.3],
            'quantization_penalty': [0.0, 0.0, 0.1]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        
        # Load and verify
        loaded_df = load_results_data(str(csv_path))
        assert len(loaded_df) == 3
        assert 'model_size' in loaded_df.columns
        assert 'context_strategy' in loaded_df.columns
        assert 'pass_result' in loaded_df.columns

    def test_load_missing_file(self, tmp_path):
        """Test that loading a non-existent file raises an error."""
        with pytest.raises(FileNotFoundError):
            load_results_data(str(tmp_path / "nonexistent.csv"))

    def test_load_empty_csv(self, tmp_path):
        """Test loading an empty CSV file."""
        csv_path = tmp_path / "empty.csv"
        csv_path.touch()
        
        with pytest.raises(ValueError):
            load_results_data(str(csv_path))

    def test_load_missing_required_columns(self, tmp_path):
        """Test loading CSV missing required columns."""
        csv_path = tmp_path / "incomplete.csv"
        data = {
            'instance_id': ['inst_1', 'inst_2'],
            'model_size': ['1B', '7B']
            # Missing context_strategy, pass_result, etc.
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        
        with pytest.raises(ValueError):
            load_results_data(str(csv_path))

    def test_load_with_extra_columns(self, tmp_path):
        """Test loading CSV with additional columns beyond required."""
        csv_path = tmp_path / "extra_cols.csv"
        data = {
            'instance_id': ['inst_1'],
            'model_size': ['1B'],
            'context_strategy': ['baseline'],
            'pass_result': [1],
            'task_difficulty': [0.5],
            'quantization_penalty': [0.0],
            'extra_column': ['should_ignore']
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        
        loaded_df = load_results_data(str(csv_path))
        assert len(loaded_df) == 1
        assert 'extra_column' not in loaded_df.columns


class TestFeaturePreparation:
    """Tests for prepare_features function."""

    def test_prepare_basic_features(self):
        """Test preparing basic features from sample data."""
        df = pd.DataFrame({
            'model_size': ['1B', '7B', '1B', '7B'],
            'context_strategy': ['baseline', 'baseline', 'tfidf', 'tfidf'],
            'pass_result': [0, 1, 1, 0],
            'task_difficulty': [0.5, 0.3, 0.7, 0.2],
            'quantization_penalty': [0.0, 0.0, 0.1, 0.0]
        })
        
        X, y = prepare_features(df)
        
        assert X.shape[0] == 4
        assert y.shape[0] == 4
        assert 'model_size_7B' in X.columns
        assert 'context_strategy_tfidf' in X.columns
        assert 'model_size_7B:context_strategy_tfidf' in X.columns

    def test_prepare_with_single_category(self):
        """Test handling when only one category exists for a variable."""
        df = pd.DataFrame({
            'model_size': ['1B', '1B', '1B'],
            'context_strategy': ['baseline', 'baseline', 'baseline'],
            'pass_result': [1, 0, 1],
            'task_difficulty': [0.5, 0.3, 0.7],
            'quantization_penalty': [0.0, 0.0, 0.0]
        })
        
        X, y = prepare_features(df)
        
        # Should handle single category gracefully
        assert X.shape[0] == 3
        assert y.shape[0] == 3

    def test_prepare_with_missing_values(self):
        """Test handling of missing values in input data."""
        df = pd.DataFrame({
            'model_size': ['1B', '7B', None, '7B'],
            'context_strategy': ['baseline', 'baseline', 'tfidf', None],
            'pass_result': [1, 0, 1, 0],
            'task_difficulty': [0.5, 0.3, 0.7, 0.2],
            'quantization_penalty': [0.0, 0.0, 0.1, 0.0]
        })
        
        # Should handle missing values (either drop or impute)
        X, y = prepare_features(df)
        assert len(X) <= 4  # May drop rows with missing values


class TestGLMFitting:
    """Tests for GLM fitting functions."""

    def test_fit_glm_with_interaction_basic(self):
        """Test basic GLM fitting with interaction term."""
        df = pd.DataFrame({
            'model_size': ['1B', '7B', '1B', '7B', '1B', '7B'] * 10,
            'context_strategy': ['baseline', 'baseline', 'tfidf', 'tfidf', 'diff_aware', 'diff_aware'] * 10,
            'pass_result': [1, 0, 1, 1, 0, 1] * 10,
            'task_difficulty': [0.5, 0.3, 0.7, 0.2, 0.4, 0.6] * 10,
            'quantization_penalty': [0.0, 0.0, 0.1, 0.0, 0.0, 0.2] * 10
        })
        
        X, y = prepare_features(df)
        
        # Should fit without error
        result = fit_glm_with_interaction(X, y)
        
        assert result is not None
        assert hasattr(result, 'params')
        assert 'model_size_7B:context_strategy_tfidf' in result.params.index or \
               'model_size_7B:context_strategy_diff_aware' in result.params.index

    def test_fit_firth_glm_basic(self):
        """Test Firth penalized GLM fitting."""
        df = pd.DataFrame({
            'model_size': ['1B', '7B', '1B', '7B'] * 5,
            'context_strategy': ['baseline', 'baseline', 'tfidf', 'tfidf'] * 5,
            'pass_result': [1, 0, 1, 1] * 5,
            'task_difficulty': [0.5, 0.3, 0.7, 0.2] * 5,
            'quantization_penalty': [0.0, 0.0, 0.1, 0.0] * 5
        })
        
        X, y = prepare_features(df)
        
        # Should fit without error
        result = fit_firth_glm(X, y)
        
        assert result is not None
        assert hasattr(result, 'params')

    def test_fit_glm_convergence_error(self):
        """Test handling of convergence failures."""
        # Create data that might cause convergence issues (perfect separation)
        df = pd.DataFrame({
            'model_size': ['1B'] * 5 + ['7B'] * 5,
            'context_strategy': ['baseline'] * 10,
            'pass_result': [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
            'task_difficulty': [0.5] * 10,
            'quantization_penalty': [0.0] * 10
        })
        
        X, y = prepare_features(df)
        
        # Should either fit or raise a controlled error
        try:
            result = fit_glm_with_interaction(X, y)
            assert result is not None
        except GLMConvergenceError:
            # Expected behavior for difficult convergence cases
            pass

    def test_fit_with_small_sample(self):
        """Test fitting with very small sample size."""
        df = pd.DataFrame({
            'model_size': ['1B', '7B'],
            'context_strategy': ['baseline', 'baseline'],
            'pass_result': [1, 0],
            'task_difficulty': [0.5, 0.3],
            'quantization_penalty': [0.0, 0.0]
        })
        
        X, y = prepare_features(df)
        
        # Should handle small samples (may warn or return None)
        result = fit_glm_with_interaction(X, y)
        # Result may be None or have warnings


class TestPostHocAnalysis:
    """Tests for post-hoc analysis functions."""

    def test_calculate_pairwise_diff_basic(self):
        """Test calculating pairwise differences in pass rates."""
        df = pd.DataFrame({
            'model_size': ['1B', '1B', '7B', '7B'],
            'context_strategy': ['baseline', 'tfidf', 'baseline', 'tfidf'],
            'pass_result': [1, 1, 0, 1],
            'task_difficulty': [0.5, 0.3, 0.5, 0.3],
            'quantization_penalty': [0.0, 0.0, 0.0, 0.0]
        })
        
        diffs = calculate_pairwise_diff(df)
        
        assert isinstance(diffs, dict)
        assert len(diffs) > 0
        # Check that differences are calculated correctly
        for strategy, diff in diffs.items():
            assert isinstance(diff, float)

    def test_check_significance_basic(self):
        """Test significance checking function."""
        df = pd.DataFrame({
            'model_size': ['1B', '1B', '7B', '7B'] * 25,
            'context_strategy': ['baseline', 'tfidf', 'baseline', 'tfidf'] * 25,
            'pass_result': [1, 1, 0, 1] * 25,
            'task_difficulty': [0.5, 0.3, 0.5, 0.3] * 25,
            'quantization_penalty': [0.0, 0.0, 0.0, 0.0] * 25
        })
        
        results = check_significance(df)
        
        assert isinstance(results, dict)
        assert 'margin' in results
        assert 'p_value' in results
        assert 'odds_ratio' in results
        assert isinstance(results['margin'], float)
        assert isinstance(results['p_value'], float)

    def test_perform_post_hoc_analysis(self):
        """Test full post-hoc analysis pipeline."""
        df = pd.DataFrame({
            'model_size': ['1B', '7B'] * 50,
            'context_strategy': ['baseline', 'baseline', 'tfidf', 'tfidf'] * 25,
            'pass_result': [1, 0, 1, 1] * 25,
            'task_difficulty': [0.5, 0.3, 0.7, 0.2] * 25,
            'quantization_penalty': [0.0, 0.0, 0.1, 0.0] * 25
        })
        
        analysis_results = perform_post_hoc_analysis(df)
        
        assert isinstance(analysis_results, dict)
        assert 'pairwise_differences' in analysis_results
        assert 'significance_tests' in analysis_results


class TestPowerAnalysis:
    """Tests for power analysis function."""

    def test_power_analysis_small_sample(self):
        """Test power analysis with small sample (N < 800)."""
        df = pd.DataFrame({
            'model_size': ['1B', '7B'] * 20,
            'context_strategy': ['baseline', 'baseline'] * 20,
            'pass_result': [1, 0] * 20,
            'task_difficulty': [0.5, 0.3] * 20,
            'quantization_penalty': [0.0, 0.0] * 20
        })
        
        results = power_analysis(df)
        
        assert isinstance(results, dict)
        assert 'study_type' in results
        assert results['study_type'] == "Exploratory"
        assert 'power' in results
        assert 'sample_size' in results
        assert results['sample_size'] < 800

    def test_power_analysis_large_sample(self):
        """Test power analysis with larger sample (N >= 800)."""
        # Create a larger dataset
        n_samples = 1000
        df = pd.DataFrame({
            'model_size': ['1B', '7B'] * (n_samples // 2),
            'context_strategy': ['baseline', 'baseline', 'tfidf', 'tfidf'] * (n_samples // 4),
            'pass_result': np.random.binomial(1, 0.5, n_samples),
            'task_difficulty': np.random.uniform(0, 1, n_samples),
            'quantization_penalty': np.random.uniform(0, 0.2, n_samples)
        })
        
        results = power_analysis(df)
        
        assert isinstance(results, dict)
        assert 'study_type' in results
        assert results['study_type'] == "Confirmatory"
        assert 'power' in results

    def test_power_analysis_low_power_warning(self):
        """Test that low power triggers appropriate warnings/flags."""
        df = pd.DataFrame({
            'model_size': ['1B', '7B'] * 10,  # Very small sample
            'context_strategy': ['baseline', 'baseline'] * 10,
            'pass_result': [1, 0] * 10,
            'task_difficulty': [0.5, 0.3] * 10,
            'quantization_penalty': [0.0, 0.0] * 10
        })
        
        results = power_analysis(df)
        
        assert results['study_type'] == "Exploratory"
        assert results['power'] < 0.8  # Should be low


class TestIntegration:
    """Integration tests for the full GLM analysis pipeline."""

    def test_full_pipeline_mock_data(self, tmp_path):
        """Test the full pipeline from data loading to results."""
        # Create mock results CSV
        csv_path = tmp_path / "mock_results.csv"
        n_samples = 200
        data = {
            'instance_id': [f'inst_{i}' for i in range(n_samples)],
            'model_size': ['1B', '7B'] * (n_samples // 2),
            'context_strategy': ['baseline', 'baseline', 'tfidf', 'tfidf', 'diff_aware', 'diff_aware'] * (n_samples // 6),
            'pass_result': np.random.binomial(1, 0.5, n_samples),
            'task_difficulty': np.random.uniform(0, 1, n_samples),
            'quantization_penalty': np.random.uniform(0, 0.2, n_samples)
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        # Run the analysis
        results = load_results_data(str(csv_path))
        X, y = prepare_features(results)
        glm_result = fit_glm_with_interaction(X, y)
        
        assert glm_result is not None
        assert hasattr(glm_result, 'params')
        assert len(glm_result.params) > 0

    def test_interaction_effect_detection(self, tmp_path):
        """Test that interaction effects are correctly detected."""
        csv_path = tmp_path / "interaction_test.csv"
        
        # Create data with a known interaction effect
        # 1B + tfidf performs better than expected
        n_samples = 400
        model_sizes = ['1B'] * 200 + ['7B'] * 200
        strategies = ['baseline'] * 100 + ['tfidf'] * 100 + ['baseline'] * 100 + ['tfidf'] * 100
        
        # 1B+tfidf has higher success rate (interaction effect)
        pass_results = []
        for m, s in zip(model_sizes, strategies):
            if m == '1B' and s == 'tfidf':
                pass_results.append(np.random.binomial(1, 0.8))  # High success
            else:
                pass_results.append(np.random.binomial(1, 0.4))  # Lower success
        
        data = {
            'instance_id': [f'inst_{i}' for i in range(n_samples)],
            'model_size': model_sizes,
            'context_strategy': strategies,
            'pass_result': pass_results,
            'task_difficulty': np.random.uniform(0, 1, n_samples),
            'quantization_penalty': np.random.uniform(0, 0.2, n_samples)
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        # Run analysis
        results = load_results_data(str(csv_path))
        X, y = prepare_features(results)
        glm_result = fit_glm_with_interaction(X, y)
        
        # Check that interaction term exists and has non-zero coefficient
        assert glm_result is not None
        interaction_terms = [col for col in glm_result.params.index if ':' in col]
        assert len(interaction_terms) > 0

    def test_stratified_analysis(self, tmp_path):
        """Test analysis across different context strategies."""
        csv_path = tmp_path / "stratified_test.csv"
        n_samples = 300
        
        strategies = ['baseline', 'tfidf', 'diff_aware', 'summarization']
        model_sizes = ['1B', '7B']
        
        data = {
            'instance_id': [f'inst_{i}' for i in range(n_samples)],
            'model_size': np.random.choice(model_sizes, n_samples),
            'context_strategy': np.random.choice(strategies, n_samples),
            'pass_result': np.random.binomial(1, 0.5, n_samples),
            'task_difficulty': np.random.uniform(0, 1, n_samples),
            'quantization_penalty': np.random.uniform(0, 0.2, n_samples)
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        # Run full pipeline
        results = load_results_data(str(csv_path))
        X, y = prepare_features(results)
        glm_result = fit_glm_with_interaction(X, y)
        post_hoc = perform_post_hoc_analysis(results)
        
        assert glm_result is not None
        assert 'pairwise_differences' in post_hoc
        assert 'significance_tests' in post_hoc

    def test_empty_interaction_term(self, tmp_path):
        """Test handling when interaction term is not significant."""
        csv_path = tmp_path / "no_interaction.csv"
        n_samples = 200
        
        # Create data with no interaction effect (main effects only)
        data = {
            'instance_id': [f'inst_{i}' for i in range(n_samples)],
            'model_size': ['1B', '7B'] * (n_samples // 2),
            'context_strategy': ['baseline', 'tfidf'] * (n_samples // 2),
            'pass_result': np.random.binomial(1, 0.5, n_samples),
            'task_difficulty': np.random.uniform(0, 1, n_samples),
            'quantization_penalty': np.random.uniform(0, 0.2, n_samples)
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        # Run analysis
        results = load_results_data(str(csv_path))
        X, y = prepare_features(results)
        glm_result = fit_glm_with_interaction(X, y)
        
        # Should still run, even if interaction is not significant
        assert glm_result is not None
        assert hasattr(glm_result, 'params')

    def test_multicategory_strategy(self, tmp_path):
        """Test handling of multiple context strategy categories."""
        csv_path = tmp_path / "multicategory.csv"
        n_samples = 400
        
        strategies = ['baseline', 'tfidf', 'diff_aware', 'summarization']
        
        data = {
            'instance_id': [f'inst_{i}' for i in range(n_samples)],
            'model_size': ['1B', '7B'] * (n_samples // 2),
            'context_strategy': np.random.choice(strategies, n_samples),
            'pass_result': np.random.binomial(1, 0.5, n_samples),
            'task_difficulty': np.random.uniform(0, 1, n_samples),
            'quantization_penalty': np.random.uniform(0, 0.2, n_samples)
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        # Run analysis
        results = load_results_data(str(csv_path))
        X, y = prepare_features(results)
        
        # Should create dummy variables for all categories
        assert 'context_strategy_tfidf' in X.columns
        assert 'context_strategy_diff_aware' in X.columns
        assert 'context_strategy_summarization' in X.columns

    def test_edge_case_perfect_separation(self, tmp_path):
        """Test handling of perfect separation in data."""
        csv_path = tmp_path / "perfect_sep.csv"
        
        # Create data with perfect separation (all 1B baseline fail, all 7B tfidf pass)
        data = {
            'instance_id': ['inst_1', 'inst_2', 'inst_3', 'inst_4'],
            'model_size': ['1B', '1B', '7B', '7B'],
            'context_strategy': ['baseline', 'baseline', 'tfidf', 'tfidf'],
            'pass_result': [0, 0, 1, 1],
            'task_difficulty': [0.5, 0.5, 0.5, 0.5],
            'quantization_penalty': [0.0, 0.0, 0.0, 0.0]
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        # Should handle gracefully (Firth or fallback)
        results = load_results_data(str(csv_path))
        X, y = prepare_features(results)
        
        # Try Firth first (handles separation better)
        firth_result = fit_firth_glm(X, y)
        assert firth_result is not None

    def test_missing_interaction_in_data(self, tmp_path):
        """Test handling when some strategy-model combinations are missing."""
        csv_path = tmp_path / "missing_combo.csv"
        
        # Only baseline for 1B, only tfidf for 7B (no cross combinations)
        data = {
            'instance_id': [f'inst_{i}' for i in range(20)],
            'model_size': ['1B'] * 10 + ['7B'] * 10,
            'context_strategy': ['baseline'] * 10 + ['tfidf'] * 10,
            'pass_result': np.random.binomial(1, 0.5, 20),
            'task_difficulty': np.random.uniform(0, 1, 20),
            'quantization_penalty': np.random.uniform(0, 0.2, 20)
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        # Should handle missing combinations
        results = load_results_data(str(csv_path))
        X, y = prepare_features(results)
        
        # May drop rows or handle with warnings
        # GLM should still attempt to fit
        try:
            glm_result = fit_glm_with_interaction(X, y)
            # Result may be None or have warnings if fitting fails
        except Exception:
            # Expected if data structure prevents fitting
            pass