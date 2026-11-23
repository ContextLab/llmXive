"""
Unit tests for Task T030: Saving plot artifacts.

These tests verify that the plot saving logic correctly generates files
in the expected directory with the expected filenames.
"""
import pytest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
import sys
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.viz import save_all_plot_artifacts
from src.config import load_config

@pytest.fixture
def sample_correlation_results():
    """Create a mock correlation results dataframe."""
    data = {
        'diversity_metric': ['Shannon', 'Shannon', 'Simpson'],
        'sleep_metric': ['Sleep Efficiency', 'Sleep Duration', 'Sleep Efficiency'],
        'r': [0.45, -0.12, 0.38],
        'p': [0.001, 0.45, 0.02],
        'q': [0.005, 0.60, 0.04],
        'is_moderate': [True, False, True],
        'is_meaningful': [True, False, True],
        'status': ['significant', 'not_significant', 'significant']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_cleaned_data():
    """Create a mock cleaned dataset with required columns."""
    np.random.seed(42)
    n_samples = 100
    data = {
        'sample_id': [f'Sample_{i}' for i in range(n_samples)],
        'shannon_diversity': np.random.normal(3.5, 0.8, n_samples),
        'simpson_diversity': np.random.normal(0.85, 0.1, n_samples),
        'sleep_efficiency': np.random.normal(85, 10, n_samples),
        'sleep_duration_hours': np.random.normal(7.5, 1.2, n_samples),
        'antibiotic_use_last_3m': [False] * n_samples
    }
    return pd.DataFrame(data)

def test_save_all_plot_artifacts_creates_files(
    sample_correlation_results, 
    sample_cleaned_data, 
    tmp_path
):
    """
    Test that save_all_plot_artifacts creates the expected files.
    """
    # Create temporary input files
    corr_path = tmp_path / "correlation_results.csv"
    data_path = tmp_path / "cleaned_data.csv"
    output_dir = tmp_path / "plots"
    
    sample_correlation_results.to_csv(corr_path, index=False)
    sample_cleaned_data.to_csv(data_path, index=False)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run the function
    save_all_plot_artifacts(
        correlation_results_path=str(corr_path),
        cleaned_data_path=str(data_path),
        output_dir=str(output_dir),
        random_seed=42
    )

    # Verify files exist
    expected_files = [
        "scatterplot_shannon_sleep.png",
        "boxplot_sleep_quartile.png"
    ]

    for filename in expected_files:
        file_path = output_dir / filename
        assert file_path.exists(), f"Expected file {filename} was not created."
        assert file_path.stat().st_size > 0, f"File {filename} is empty."

def test_save_all_plot_artifacts_handles_missing_correlations(
    sample_cleaned_data, 
    tmp_path
):
    """
    Test behavior when there are no significant correlations to plot.
    The function should still create the boxplot (if logic permits) 
    or handle the missing scatterplot gracefully.
    """
    # Create empty or non-significant correlation results
    empty_corr = pd.DataFrame(columns=['diversity_metric', 'sleep_metric', 'r', 'p', 'q', 'is_meaningful', 'status'])
    
    corr_path = tmp_path / "correlation_results.csv"
    data_path = tmp_path / "cleaned_data.csv"
    output_dir = tmp_path / "plots"
    
    empty_corr.to_csv(corr_path, index=False)
    sample_cleaned_data.to_csv(data_path, index=False)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Should not raise an error even if no meaningful correlations exist
    # (depending on implementation, it might skip scatterplot but still run boxplot)
    try:
        save_all_plot_artifacts(
            correlation_results_path=str(corr_path),
            cleaned_data_path=str(data_path),
            output_dir=str(output_dir),
            random_seed=42
        )
    except Exception as e:
        # If it fails, it should be a clear error, not a silent failure
        pytest.fail(f"save_all_plot_artifacts raised an unexpected exception: {e}")

def test_save_all_plot_artifacts_uses_correct_paths(
    sample_correlation_results, 
    sample_cleaned_data, 
    tmp_path
):
    """
    Test that the function uses the provided paths correctly.
    """
    corr_path = tmp_path / "custom_corr.csv"
    data_path = tmp_path / "custom_data.csv"
    output_dir = tmp_path / "custom_plots"
    
    sample_correlation_results.to_csv(corr_path, index=False)
    sample_cleaned_data.to_csv(data_path, index=False)
    output_dir.mkdir(parents=True, exist_ok=True)

    save_all_plot_artifacts(
        correlation_results_path=str(corr_path),
        cleaned_data_path=str(data_path),
        output_dir=str(output_dir),
        random_seed=42
    )

    # Verify files are in the custom output directory
    assert (output_dir / "scatterplot_shannon_sleep.png").exists()
    assert (output_dir / "boxplot_sleep_quartile.png").exists()