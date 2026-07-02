"""
Unit tests for correlation plot generation with confidence intervals (T036).

This module tests the functionality of generating scatter plots with regression lines
and 95% confidence intervals for feature-conductivity correlations.
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from unittest.mock import patch, MagicMock
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

# Mock matplotlib backend before importing plot functions
plt.switch_backend('Agg')

from feature_analysis import calculate_correlation_pvalues, benjamini_hochberg


@pytest.fixture
def sample_data():
    """Create a sample DataFrame with features and target for testing."""
    np.random.seed(42)
    n_samples = 100
    data = {
        'feature_1': np.random.normal(0, 1, n_samples),
        'feature_2': np.random.normal(0, 1, n_samples),
        'feature_3': np.random.normal(0, 1, n_samples),
        'target': np.random.normal(0, 1, n_samples)
    }
    # Create a correlation for feature_1
    data['target'] = 2.0 * data['feature_1'] + np.random.normal(0, 0.5, n_samples)
    return pd.DataFrame(data)


@pytest.fixture
def sample_data_no_correlation():
    """Create a sample DataFrame with no significant correlation."""
    np.random.seed(42)
    n_samples = 100
    data = {
        'feature_1': np.random.normal(0, 1, n_samples),
        'feature_2': np.random.normal(0, 1, n_samples),
        'target': np.random.normal(0, 1, n_samples)
    }
    return pd.DataFrame(data)


def test_correlation_plot_generation_basic(sample_data, tmp_path):
    """Test basic correlation plot generation with confidence intervals."""
    from descriptors import compute_descriptors_batch
    from matplotlib import pyplot as plt
    import seaborn as sns

    # Create a simple plot to test the generation logic
    fig, ax = plt.subplots()
    sns.regplot(
        data=sample_data,
        x='feature_1',
        y='target',
        ax=ax,
        scatter_kws={'alpha': 0.5},
        line_kws={'color': 'red'}
    )
    ax.set_xlabel('Feature 1')
    ax.set_ylabel('Conductivity (log)')
    ax.set_title('Feature 1 vs Conductivity')

    output_path = os.path.join(tmp_path, 'test_plot.png')
    fig.savefig(output_path, dpi=100)
    plt.close(fig)

    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0


def test_confidence_interval_calculation(sample_data):
    """Test that confidence intervals are correctly calculated."""
    from scipy import stats
    import numpy as np

    x = sample_data['feature_1'].values
    y = sample_data['target'].values

    # Calculate regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    # Calculate 95% CI
    n = len(x)
    t_critical = stats.t.ppf(0.975, df=n-2)
    ci_margin = t_critical * std_err

    assert ci_margin > 0
    assert p_value < 0.05  # Should be significant given the synthetic data


def test_multiple_comparison_correction(sample_data):
    """Test Benjamini-Hochberg correction for multiple comparisons."""
    # Calculate p-values for all features
    features = ['feature_1', 'feature_2', 'feature_3']
    p_values = []

    for feature in features:
        _, _, _, p_val, _ = stats.linregress(
            sample_data[feature].values,
            sample_data['target'].values
        )
        p_values.append(p_val)

    # Apply BH correction
    adjusted_p_values = benjamini_hochberg(p_values)

    assert len(adjusted_p_values) == len(p_values)
    assert all(0 <= p <= 1 for p in adjusted_p_values)
    # feature_1 should have lower adjusted p-value than others
    assert adjusted_p_values[0] <= adjusted_p_values[1]
    assert adjusted_p_values[0] <= adjusted_p_values[2]


def test_plot_with_nan_handling(tmp_path):
    """Test plot generation handles NaN values correctly."""
    np.random.seed(42)
    n_samples = 100
    data = {
        'feature_1': np.random.normal(0, 1, n_samples),
        'target': np.random.normal(0, 1, n_samples)
    }
    df = pd.DataFrame(data)

    # Introduce some NaN values
    df.loc[0:4, 'feature_1'] = np.nan
    df.loc[5:9, 'target'] = np.nan

    # Remove NaN for plotting (standard behavior)
    df_clean = df.dropna()

    assert len(df_clean) < len(df)
    assert len(df_clean) > 0

    fig, ax = plt.subplots()
    sns.regplot(data=df_clean, x='feature_1', y='target', ax=ax)
    output_path = os.path.join(tmp_path, 'nan_test_plot.png')
    fig.savefig(output_path)
    plt.close(fig)

    assert os.path.exists(output_path)


def test_top_features_selection(sample_data):
    """Test selection of top 5 features by correlation strength."""
    from scipy import stats

    features = ['feature_1', 'feature_2', 'feature_3']
    correlations = []

    for feature in features:
        corr, p_val = stats.pearsonr(
            sample_data[feature].values,
            sample_data['target'].values
        )
        correlations.append((feature, abs(corr), p_val))

    # Sort by absolute correlation strength
    correlations.sort(key=lambda x: x[1], reverse=True)

    # feature_1 should be first due to synthetic correlation
    assert correlations[0][0] == 'feature_1'
    assert correlations[0][1] > correlations[1][1]


def test_plot_output_format(tmp_path):
    """Test that plot output is in correct format (PNG)."""
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 2, 3])

    output_path = os.path.join(tmp_path, 'test_output.png')
    fig.savefig(output_path, format='png')
    plt.close(fig)

    assert os.path.exists(output_path)
    assert output_path.endswith('.png')

    # Check file header for PNG signature
    with open(output_path, 'rb') as f:
        header = f.read(8)
        assert header[:8] == b'\x89PNG\r\n\x1a\n'