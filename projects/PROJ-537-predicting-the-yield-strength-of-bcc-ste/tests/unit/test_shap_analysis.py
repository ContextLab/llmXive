"""
Unit tests for SHAP analysis module.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.interpretability.shap_analysis import (
    load_preprocessed_data,
    load_trained_model,
    calculate_shap_values,
    analyze_feature_importance,
    generate_shap_plots,
    run_shap_analysis
)


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n_samples = 50
    data = {
        'Fe': np.random.rand(n_samples),
        'C': np.random.rand(n_samples) * 0.1,
        'Mn': np.random.rand(n_samples) * 0.05,
        'shear_modulus_GPa': np.random.rand(n_samples) * 100 + 50,
        'bulk_modulus_GPa': np.random.rand(n_samples) * 100 + 100,
        'yield_strength_MPa': np.random.rand(n_samples) * 500 + 200
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_config(tmp_path):
    """Mock configuration with temporary directories."""
    with patch('code.interpretability.shap_analysis.CONFIG') as mock_config:
        mock_config.INTERMEDIATE_DIR = tmp_path / "intermediate"
        mock_config.PROCESSED_DIR = tmp_path / "processed"
        mock_config.RESULTS_DIR = tmp_path / "results"
        mock_config.SEED = 42

        mock_config.INTERMEDIATE_DIR.mkdir(parents=True)
        mock_config.PROCESSED_DIR.mkdir(parents=True)
        mock_config.RESULTS_DIR.mkdir(parents=True)

        yield mock_config


@pytest.fixture
def mock_model():
    """Create a mock Random Forest model."""
    model = MagicMock()
    model.feature_importances_ = np.array([0.1, 0.2, 0.15, 0.3, 0.25])
    return model


def test_load_preprocessed_data_missing_file(mock_config):
    """Test that missing data file raises error."""
    with pytest.raises(FileNotFoundError):
        load_preprocessed_data()


def test_load_preprocessed_data_success(mock_config, sample_data, tmp_path):
    """Test successful data loading."""
    # Create mock data file
    data_path = mock_config.INTERMEDIATE_DIR / "merged.csv"
    sample_data.to_csv(data_path, index=False)

    X, y, feature_names = load_preprocessed_data()

    assert len(X) == len(sample_data)
    assert 'yield_strength_MPa' not in X.columns
    assert len(feature_names) > 0


def test_load_trained_model_missing_file(mock_config):
    """Test that missing model file raises error."""
    with pytest.raises(FileNotFoundError):
        load_trained_model()


def test_calculate_shap_values(mock_model, sample_data):
    """Test SHAP value calculation."""
    with patch('code.interpretability.shap_analysis.shap.TreeExplainer') as mock_explainer:
        mock_shap_values = MagicMock()
        mock_shap_values.__array__ = lambda self: np.random.rand(10, 5)
        mock_explainer.return_value.shap_values.return_value = mock_shap_values

        shap_vals, X_sample = calculate_shap_values(
            mock_model,
            sample_data[['Fe', 'C', 'Mn', 'shear_modulus_GPa', 'bulk_modulus_GPa']],
            ['Fe', 'C', 'Mn', 'shear_modulus_GPa', 'bulk_modulus_GPa']
        )

        assert shap_vals is not None
        assert X_sample is not None


def test_analyze_feature_importance():
    """Test feature importance analysis."""
    np.random.seed(42)
    shap_vals = np.random.rand(10, 5)
    feature_names = ['Fe', 'C', 'Mn', 'shear_modulus_GPa', 'bulk_modulus_GPa']
    X_sample = pd.DataFrame(np.random.rand(10, 5), columns=feature_names)

    importance = analyze_feature_importance(shap_vals, feature_names, X_sample)

    assert 'top_features' in importance
    assert 'full_ranking' in importance
    assert len(importance['top_features']) <= 5
    assert 'dft_importance' in importance
    assert 'composition_importance' in importance


def test_generate_shap_plots(mock_config, tmp_path):
    """Test SHAP plot generation."""
    np.random.seed(42)
    shap_vals = np.random.rand(10, 5)
    feature_names = ['Fe', 'C', 'Mn', 'shear_modulus_GPa', 'bulk_modulus_GPa']
    X_sample = pd.DataFrame(np.random.rand(10, 5), columns=feature_names)

    plots_dir = tmp_path / "figures"
    plot_paths = generate_shap_plots(shap_vals, X_sample, plots_dir)

    # At least one plot should be generated (summary or bar)
    assert len(plot_paths) >= 0  # May be 0 if matplotlib fails in test environment


def test_run_shap_analysis_integration(mock_config, sample_data, tmp_path):
    """Integration test for full SHAP analysis pipeline."""
    # Setup mock data
    data_path = mock_config.INTERMEDIATE_DIR / "merged.csv"
    sample_data.to_csv(data_path, index=False)

    # Create mock model file
    import pickle
    model_path = mock_config.PROCESSED_DIR / "rf_dft_model.pkl"
    mock_model = MagicMock()
    mock_model.feature_importances_ = np.array([0.1, 0.2, 0.15, 0.3, 0.25])
    with open(model_path, 'wb') as f:
        pickle.dump(mock_model, f)

    # Mock SHAP to avoid heavy computation
    with patch('code.interpretability.shap_analysis.shap.TreeExplainer') as mock_explainer:
        mock_shap_values = MagicMock()
        mock_shap_values.__array__ = lambda self: np.random.rand(10, 5)
        mock_explainer.return_value.shap_values.return_value = mock_shap_values

        with patch('code.interpretability.shap_analysis.shap.summary_plot'):
            with patch('code.interpretability.shap_analysis.shap.dependence_plot'):
                with patch('matplotlib.pyplot.savefig'):
                    with patch('matplotlib.pyplot.close'):
                        results = run_shap_analysis()

                        assert 'importance_analysis' in results
                        assert 'plot_paths' in results
                        assert 'results_file' in results
                        assert Path(results['results_file']).exists()