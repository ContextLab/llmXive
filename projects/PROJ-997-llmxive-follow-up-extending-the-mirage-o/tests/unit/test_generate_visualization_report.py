"""
Unit tests for T039: generate_visualization_report.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest
import pandas as pd
import numpy as np

from src.cli.generate_visualization_report import (
    load_consistency_report,
    load_t_test_results,
    load_metrics_files,
    load_test_data,
    create_scatter_plot,
    create_bar_chart,
    create_box_plot,
    generate_markdown_report
)


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    return data_dir


@pytest.fixture
def mock_consistency_report():
    """Mock consistency report data."""
    return {
        "per_level_correlations": {
            "INT4": 0.85,
            "INT8": 0.88,
            "FP8": 0.82
        },
        "global_consistency_metric": 0.85,
        "per_level_satisfaction_pct": {
            "INT4": 85.5,
            "INT8": 88.2,
            "FP8": 82.1
        }
    }


@pytest.fixture
def mock_t_test_results():
    """Mock t-test results data."""
    return {
        "p_value": 0.12,
        "statistic": 1.56,
        "method": "bonferroni_corrected_t_test",
        "adjusted_alpha": 0.0167,
        "normality_check": {
            "shapiro_p_value": 0.25,
            "method_used": "shapiro_wilk"
        }
    }


@pytest.fixture
def mock_baseline_metrics():
    """Mock baseline metrics data."""
    return {
        "acceptance_rate": 0.75,
        "reasoning_score": 0.82,
        "timing_metadata": {
            "total_time": 120.5,
            "inference_only_time": 115.0,
            "policy_evaluation_time": 5.5
        }
    }


@pytest.fixture
def mock_proxy_metrics():
    """Mock proxy metrics data."""
    return {
        "acceptance_rate": 0.73,
        "reasoning_score": 0.80,
        "timing_metadata": {
            "total_time": 15.2,
            "prediction_only_time": 0.5,
            "policy_evaluation_time": 0.5
        }
    }


@pytest.fixture
def mock_test_df():
    """Mock test dataframe."""
    data = {
        "predicted_gap": np.random.uniform(0, 0.2, 100),
        "actual_gap": np.random.uniform(0, 0.2, 100),
        "quantization_level": np.random.choice(["INT4", "INT8", "FP8"], 100)
    }
    return pd.DataFrame(data)


def test_load_consistency_report_success(temp_data_dir, mock_consistency_report):
    """Test successful loading of consistency report."""
    report_path = temp_data_dir / "consistency_report.json"
    with open(report_path, 'w') as f:
        json.dump(mock_consistency_report, f)
    
    result = load_consistency_report()
    assert result == mock_consistency_report
    assert "per_level_correlations" in result


def test_load_consistency_report_file_not_found(temp_data_dir):
    """Test FileNotFoundError when report is missing."""
    with pytest.raises(FileNotFoundError):
        load_consistency_report()


def test_load_t_test_results_success(temp_data_dir, mock_t_test_results):
    """Test successful loading of t-test results."""
    report_path = temp_data_dir / "t_test_results.json"
    with open(report_path, 'w') as f:
        json.dump(mock_t_test_results, f)
    
    result = load_t_test_results()
    assert result == mock_t_test_results
    assert "p_value" in result


def test_load_metrics_files_success(temp_data_dir, mock_baseline_metrics, mock_proxy_metrics):
    """Test loading of baseline and proxy metrics."""
    baseline_path = temp_data_dir / "baseline_metrics.json"
    proxy_path = temp_data_dir / "proxy_metrics.json"
    
    with open(baseline_path, 'w') as f:
        json.dump(mock_baseline_metrics, f)
    with open(proxy_path, 'w') as f:
        json.dump(mock_proxy_metrics, f)
    
    # Patch the load_metrics_from_json function
    with patch('src.cli.generate_visualization_report.load_metrics_from_json') as mock_load:
        mock_load.side_effect = [mock_baseline_metrics, mock_proxy_metrics]
        baseline, proxy = load_metrics_files()
        assert baseline == mock_baseline_metrics
        assert proxy == mock_proxy_metrics


def test_load_test_data_success(temp_data_dir, mock_test_df):
    """Test loading of test data."""
    test_path = temp_data_dir / "test.parquet"
    mock_test_df.to_parquet(test_path)
    
    # Patch to return our mock dataframe
    with patch('src.cli.generate_visualization_report.pd.read_parquet') as mock_read:
        mock_read.return_value = mock_test_df
        df = load_test_data()
        assert isinstance(df, pd.DataFrame)
        assert "predicted_gap" in df.columns
        assert "quantization_level" in df.columns


def test_load_test_data_missing_columns(temp_data_dir, mock_test_df):
    """Test ValueError when required columns are missing."""
    test_path = temp_data_dir / "test.parquet"
    # Create df without required columns
    bad_df = mock_test_df.drop(columns=["predicted_gap"])
    bad_df.to_parquet(test_path)
    
    with patch('src.cli.generate_visualization_report.pd.read_parquet') as mock_read:
        mock_read.return_value = bad_df
        with pytest.raises(ValueError):
            load_test_data()


@patch('src.cli.generate_visualization_report.plt')
def test_create_scatter_plot(mock_plt, temp_data_dir, mock_test_df):
    """Test scatter plot creation."""
    output_path = temp_data_dir / "scatter.png"
    
    # Mock plt functions
    mock_plt.figure.return_value = MagicMock()
    mock_plt.scatter = MagicMock()
    mock_plt.plot = MagicMock()
    mock_plt.xlabel = MagicMock()
    mock_plt.ylabel = MagicMock()
    mock_plt.title = MagicMock()
    mock_plt.legend = MagicMock()
    mock_plt.grid = MagicMock()
    mock_plt.tight_layout = MagicMock()
    mock_plt.savefig = MagicMock()
    mock_plt.close = MagicMock()
    
    result = create_scatter_plot(mock_test_df, output_path)
    
    assert "scatter.png" in result
    mock_plt.savefig.assert_called_once()
    mock_plt.close.assert_called_once()


@patch('src.cli.generate_visualization_report.plt')
def test_create_bar_chart(mock_plt, temp_data_dir, mock_consistency_report):
    """Test bar chart creation."""
    output_path = temp_data_dir / "bar.png"
    
    mock_plt.figure.return_value = MagicMock()
    mock_plt.bar = MagicMock()
    mock_plt.text = MagicMock()
    mock_plt.ylabel = MagicMock()
    mock_plt.title = MagicMock()
    mock_plt.ylim = MagicMock()
    mock_plt.grid = MagicMock()
    mock_plt.tight_layout = MagicMock()
    mock_plt.savefig = MagicMock()
    mock_plt.close = MagicMock()
    
    result = create_bar_chart(mock_consistency_report, output_path)
    
    assert "bar.png" in result
    mock_plt.savefig.assert_called_once()


@patch('src.cli.generate_visualization_report.plt')
@patch('src.cli.generate_visualization_report.np')
def test_create_box_plot(mock_np, mock_plt, temp_data_dir, mock_baseline_metrics, mock_proxy_metrics):
    """Test box plot creation."""
    output_path = temp_data_dir / "box.png"
    
    mock_plt.figure.return_value = MagicMock()
    mock_plt.boxplot = MagicMock(return_value={'boxes': [MagicMock(), MagicMock()]})
    mock_plt.text = MagicMock()
    mock_plt.ylabel = MagicMock()
    mock_plt.title = MagicMock()
    mock_plt.ylim = MagicMock()
    mock_plt.grid = MagicMock()
    mock_plt.tight_layout = MagicMock()
    mock_plt.savefig = MagicMock()
    mock_plt.close = MagicMock()
    
    mock_np.random.seed = MagicMock()
    mock_np.random.normal = MagicMock(side_effect=[
        np.random.normal(0.82, 0.15, 100),
        np.random.normal(0.80, 0.15, 100)
    ])
    mock_np.clip = MagicMock(side_effect=[
        np.clip(np.random.normal(0.82, 0.15, 100), 0, 1),
        np.clip(np.random.normal(0.80, 0.15, 100), 0, 1)
    ])
    
    result = create_box_plot(mock_baseline_metrics, mock_proxy_metrics, output_path)
    
    assert "box.png" in result
    mock_plt.savefig.assert_called_once()


def test_generate_markdown_report(temp_data_dir, mock_consistency_report, mock_t_test_results,
                                  mock_baseline_metrics, mock_proxy_metrics):
    """Test markdown report generation."""
    scatter_path = "figures/scatter.png"
    bar_path = "figures/bar.png"
    box_path = "figures/box.png"
    
    report = generate_markdown_report(
        scatter_path, bar_path, box_path,
        mock_consistency_report, mock_t_test_results,
        mock_baseline_metrics, mock_proxy_metrics
    )
    
    assert "# Visualization Report" in report
    assert "## 1. Predicted vs Actual Policy Gap" in report
    assert "## 2. Bound Satisfaction Rate" in report
    assert "## 3. Reasoning Score Comparison" in report
    assert "## 4. Performance Summary" in report
    assert scatter_path in report
    assert bar_path in report
    assert box_path in report
    assert "bonferroni_corrected_t_test" in report