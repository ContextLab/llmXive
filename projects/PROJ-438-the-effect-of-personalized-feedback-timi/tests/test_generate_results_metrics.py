"""
Unit tests for generate_results_metrics.py
"""
import os
import sys
import pandas as pd
import pytest
from pathlib import Path
import tempfile
import shutil

# Add code directory to path
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
sys.path.insert(0, str(code_dir))

from generate_results_metrics import (
    load_effect_sizes,
    load_sensitivity_stats,
    load_stability_metrics,
    load_flip_rate_metrics,
    merge_metrics,
    save_results_metrics
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_load_effect_sizes_missing_file(temp_data_dir):
    """Test that load_effect_sizes raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_effect_sizes(temp_data_dir / "nonexistent.csv")

def test_load_sensitivity_stats_missing_file(temp_data_dir):
    """Test that load_sensitivity_stats raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_sensitivity_stats(temp_data_dir / "nonexistent.csv")

def test_merge_metrics_basic():
    """Test merging of basic metric dataframes."""
    effect_df = pd.DataFrame({
        'comparison': ['A vs B', 'A vs C'],
        'coef': [0.5, 0.8],
        'p_value': [0.01, 0.04]
    })

    stability_df = pd.DataFrame({
        'comparison': ['A vs B', 'A vs C'],
        'stability_rate': [0.9, 0.85]
    })

    flip_df = pd.DataFrame({
        'comparison': ['A vs B', 'A vs C'],
        'flip_rate': [0.1, 0.15]
    })

    sensitivity_df = pd.DataFrame({
        'avg_p_value': 0.025,
        'significant_count': 2,
        'total_count': 10
    })

    result = merge_metrics(effect_df, sensitivity_df, stability_df, flip_df)

    assert len(result) == 2
    assert 'coef' in result.columns
    assert 'stability_rate' in result.columns
    assert 'flip_rate' in result.columns
    assert result.loc[result['comparison'] == 'A vs B', 'coef'].iloc[0] == 0.5

def test_merge_metrics_missing_comparison():
    """Test merging when comparison column is missing."""
    effect_df = pd.DataFrame({'coef': [0.5]})
    stability_df = pd.DataFrame({'stability_rate': [0.9]})
    flip_df = pd.DataFrame({'flip_rate': [0.1]})
    sensitivity_df = pd.DataFrame({'avg_p_value': 0.02})

    with pytest.raises(ValueError):
        merge_metrics(effect_df, sensitivity_df, stability_df, flip_df)

def test_save_results_metrics(temp_data_dir):
    """Test saving results to CSV."""
    df = pd.DataFrame({
        'comparison': ['Test'],
        'value': [1.0]
    })
    output_path = temp_data_dir / "test_results.csv"

    save_results_metrics(df, output_path)

    assert output_path.exists()
    loaded = pd.read_csv(output_path)
    assert len(loaded) == 1
    assert loaded['comparison'].iloc[0] == 'Test'