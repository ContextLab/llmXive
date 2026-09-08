"""
Unit tests for code/evaluate.py.
These tests verify the statistical significance and interaction analysis logic.
"""
import json
import os
import sys
import tempfile
import pickle
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score

# Adjust import path to match project structure
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluate import (
    load_models,
    calculate_permutation_importance,
    run_permutation_test,
    calculate_shap_interactions,
    generate_statistical_report,
    generate_shap_report,
    main
)
from config import get_project_root


class TestEvaluateModule:
    """Test suite for evaluate.py functions."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Create necessary subdirectories
            (tmp_path / "models").mkdir()
            (tmp_path / "reports").mkdir()
            (tmp_path / "processed").mkdir()
            yield tmp_path

    @pytest.fixture
    def sample_data(self):
        """Create sample engineered data for testing."""
        data = {
            'cold_work_pct': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            'Mn_wt': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            'Mg_wt': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            'Si_wt': [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5],
            'Cu_wt': [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
            'annealing_temp_K': [400, 450, 500, 550, 600, 650, 700, 750, 800, 850],
            'time_to_peak_min': [100, 90, 80, 70, 60, 50, 40, 30, 20, 10],
            'cold_work_Mn': [1, 4, 9, 16, 25, 36, 49, 64, 81, 100],
            'cold_work_Mg': [1, 4, 9, 16, 25, 36, 49, 64, 81, 100],
            'cold_work_Si': [0.5, 2, 4.5, 8, 12.5, 18, 24.5, 32, 40.5, 50],
            'cold_work_Cu': [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def mock_models(self, temp_dirs, sample_data):
        """Create mock trained models for testing."""
        # Create a simple additive model (without interaction features)
        additive_features = ['cold_work_pct', 'Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt', 'annealing_temp_K']
        additive_model = RandomForestRegressor(n_estimators=5, random_state=42, n_jobs=1)
        additive_model.fit(sample_data[additive_features], sample_data['time_to_peak_min'])

        # Create a simple interaction model (with interaction features)
        interaction_features = additive_features + ['cold_work_Mn', 'cold_work_Mg', 'cold_work_Si', 'cold_work_Cu']
        interaction_model = RandomForestRegressor(n_estimators=5, random_state=42, n_jobs=1)
        interaction_model.fit(sample_data[interaction_features], sample_data['time_to_peak_min'])

        # Save models
        additive_path = temp_dirs / "models" / "additive_model.pkl"
        interaction_path = temp_dirs / "models" / "kinetic_model.pkl"

        with open(additive_path, 'wb') as f:
            pickle.dump(additive_model, f)
        with open(interaction_path, 'wb') as f:
            pickle.dump(interaction_model, f)

        return additive_model, interaction_model, additive_path, interaction_path

    def test_load_models(self, mock_models, temp_dirs):
        """Test loading models from disk."""
        additive_model, interaction_model, additive_path, interaction_path = mock_models

        # Mock the path to use temp directory
        with patch('evaluate.get_project_root', return_value=temp_dirs):
            loaded_additive, loaded_interaction = load_models()

            assert loaded_additive is not None
            assert loaded_interaction is not None
            assert isinstance(loaded_additive, RandomForestRegressor)
            assert isinstance(loaded_interaction, RandomForestRegressor)

    def test_calculate_permutation_importance(self, mock_models, sample_data):
        """Test permutation importance calculation for interaction terms."""
        additive_model, interaction_model, _, _ = mock_models

        interaction_features = ['cold_work_Mn', 'cold_work_Mg', 'cold_work_Si', 'cold_work_Cu']
        X = sample_data[['cold_work_pct', 'Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt', 'annealing_temp_K'] + interaction_features]
        y = sample_data['time_to_peak_min']

        importance = calculate_permutation_importance(interaction_model, X, y, interaction_features, n_repeats=3, random_state=42)

        assert 'permutation_importance' in importance
        assert 'interaction_importance' in importance
        assert isinstance(importance['permutation_importance'], float)
        assert isinstance(importance['interaction_importance'], dict)
        assert len(importance['interaction_importance']) == len(interaction_features)

    def test_run_permutation_test(self, mock_models, sample_data):
        """Test the full permutation test logic."""
        additive_model, interaction_model, _, _ = mock_models

        interaction_features = ['cold_work_Mn', 'cold_work_Mg', 'cold_work_Si', 'cold_work_Cu']
        X = sample_data[['cold_work_pct', 'Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt', 'annealing_temp_K'] + interaction_features]
        y = sample_data['time_to_peak_min']

        # Run permutation test with small n_permutations for speed
        result = run_permutation_test(interaction_model, X, y, interaction_features, n_permutations=5, random_state=42)

        assert 'p_value' in result
        assert 'test_statistic' in result
        assert 'conclusion' in result
        assert isinstance(result['p_value'], float)
        assert isinstance(result['test_statistic'], float)
        assert result['conclusion'] in ['significant', 'not_significant']

    def test_generate_statistical_report(self, mock_models, sample_data, temp_dirs):
        """Test generation of statistical significance report."""
        additive_model, interaction_model, _, _ = mock_models

        interaction_features = ['cold_work_Mn', 'cold_work_Mg', 'cold_work_Si', 'cold_work_Cu']
        X = sample_data[['cold_work_pct', 'Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt', 'annealing_temp_K'] + interaction_features]
        y = sample_data['time_to_peak_min']

        # Run permutation test
        perm_result = run_permutation_test(interaction_model, X, y, interaction_features, n_permutations=5, random_state=42)

        # Calculate permutation importance
        perm_importance = calculate_permutation_importance(interaction_model, X, y, interaction_features, n_repeats=3, random_state=42)

        # Generate report
        report = generate_statistical_report(perm_result, perm_importance)

        assert 'p_value' in report
        assert 'test_statistic' in report
        assert 'conclusion' in report
        assert 'permutation_importance' in report
        assert 'interaction_importance' in report
        assert report['conclusion'] in ['significant', 'not_significant']

        # Write to file
        report_path = temp_dirs / "reports" / "statistical_significance.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        assert report_path.exists()

    def test_generate_shap_report(self, mock_models, sample_data, temp_dirs):
        """Test SHAP interaction report generation (mocked)."""
        _, interaction_model, _, _ = mock_models

        interaction_features = ['cold_work_Mn', 'cold_work_Mg', 'cold_work_Si', 'cold_work_Cu']
        X = sample_data[['cold_work_pct', 'Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt', 'annealing_temp_K'] + interaction_features]

        # Mock shap to avoid heavy computation in unit tests
        with patch('evaluate.shap.TreeExplainer') as mock_explainer_class:
            mock_explainer = MagicMock()
            mock_explainer.shap_values.return_value = np.random.rand(len(X), X.shape[1], X.shape[1])
            mock_explainer_class.return_value = mock_explainer

            report = generate_shap_report(interaction_model, X, interaction_features)

            assert 'top_features' in report
            assert 'interaction_terms' in report
            assert 'pure_aluminum_flag' in report
            assert isinstance(report['top_features'], list)
            assert isinstance(report['interaction_terms'], list)
            assert report['pure_aluminum_flag'] is False

    def test_main_function(self, mock_models, sample_data, temp_dirs):
        """Test the main function entry point."""
        additive_model, interaction_model, _, _ = mock_models

        # Create sample data file
        data_path = temp_dirs / "processed" / "engineered_features.csv"
        sample_data.to_csv(data_path, index=False)

        # Mock paths
        with patch('evaluate.get_project_root', return_value=temp_dirs):
            with patch('evaluate.load_models', return_value=(additive_model, interaction_model)):
                # Mock shap to avoid heavy computation
                with patch('evaluate.shap.TreeExplainer') as mock_explainer_class:
                    mock_explainer = MagicMock()
                    mock_explainer.shap_values.return_value = np.random.rand(len(sample_data), sample_data.shape[1], sample_data.shape[1])
                    mock_explainer_class.return_value = mock_explainer

                    # Run main
                    main()

                    # Check that reports were generated
                    stat_report_path = temp_dirs / "reports" / "statistical_significance.json"
                    shap_report_path = temp_dirs / "reports" / "shap_interaction_report.json"

                    assert stat_report_path.exists()
                    assert shap_report_path.exists()

                    # Verify content
                    with open(stat_report_path, 'r') as f:
                        stat_data = json.load(f)
                        assert 'p_value' in stat_data

                    with open(shap_report_path, 'r') as f:
                        shap_data = json.load(f)
                        assert 'top_features' in shap_data

    def test_pure_aluminum_detection(self, temp_dirs):
        """Test pure aluminum flag detection in reports."""
        # Create pure aluminum data (zero variance in composition)
        pure_data = {
            'cold_work_pct': [10, 20, 30, 40, 50],
            'Mn_wt': [0.0, 0.0, 0.0, 0.0, 0.0],
            'Mg_wt': [0.0, 0.0, 0.0, 0.0, 0.0],
            'Si_wt': [0.0, 0.0, 0.0, 0.0, 0.0],
            'Cu_wt': [0.0, 0.0, 0.0, 0.0, 0.0],
            'annealing_temp_K': [400, 450, 500, 550, 600],
            'time_to_peak_min': [100, 90, 80, 70, 60],
            'cold_work_Mn': [0, 0, 0, 0, 0],
            'cold_work_Mg': [0, 0, 0, 0, 0],
            'cold_work_Si': [0, 0, 0, 0, 0],
            'cold_work_Cu': [0, 0, 0, 0, 0]
        }
        pure_df = pd.DataFrame(pure_data)

        # Mock shap to avoid heavy computation
        with patch('evaluate.shap.TreeExplainer') as mock_explainer_class:
            mock_explainer = MagicMock()
            mock_explainer.shap_values.return_value = np.random.rand(len(pure_df), pure_df.shape[1], pure_df.shape[1])
            mock_explainer_class.return_value = mock_explainer

            # Create a dummy model
            model = RandomForestRegressor(n_estimators=5, random_state=42, n_jobs=1)
            model.fit(pure_df.drop('time_to_peak_min', axis=1), pure_df['time_to_peak_min'])

            report = generate_shap_report(model, pure_df.drop('time_to_peak_min', axis=1), ['cold_work_Mn'])

            assert report['pure_aluminum_flag'] is True

if __name__ == '__main__':
    pytest.main([__file__, '-v'])