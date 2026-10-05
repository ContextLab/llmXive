"""
Unit tests for generate_sensitivity_summary module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.generate_sensitivity_summary import (
    load_sensitivity_data,
    compute_summary_stats,
    generate_summary_text,
    write_summary
)


def test_load_sensitivity_data_missing_file():
    """Test that loading a missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_sensitivity_data("nonexistent.csv")


def test_load_sensitivity_data_missing_columns():
    """Test that loading a file with missing columns raises ValueError."""
    df = pd.DataFrame({
        'threshold': [1.0, 2.0],
        'mond_pass_rate': [0.5, 0.6]
        # Missing 'nfw_pass_rate'
    })

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name

    try:
        with pytest.raises(ValueError) as exc_info:
            load_sensitivity_data(temp_path)
        assert "missing required columns" in str(exc_info.value)
    finally:
        os.unlink(temp_path)


def test_load_sensitivity_data_success():
    """Test successful loading of valid sensitivity data."""
    df = pd.DataFrame({
        'threshold': [1.0, 1.25, 1.5, 1.75],
        'mond_pass_rate': [0.8, 0.75, 0.7, 0.65],
        'nfw_pass_rate': [0.6, 0.65, 0.7, 0.75]
    })

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name

    try:
        loaded_df = load_sensitivity_data(temp_path)
        assert len(loaded_df) == 4
        assert set(loaded_df.columns) == {'threshold', 'mond_pass_rate', 'nfw_pass_rate'}
        assert loaded_df['threshold'].tolist() == [1.0, 1.25, 1.5, 1.75]
    finally:
        os.unlink(temp_path)


def test_compute_summary_stats():
    """Test computation of summary statistics."""
    df = pd.DataFrame({
        'threshold': [1.0, 1.25, 1.5, 1.75],
        'mond_pass_rate': [0.8, 0.75, 0.7, 0.65],
        'nfw_pass_rate': [0.6, 0.65, 0.7, 0.75]
    })

    stats = compute_summary_stats(df)

    assert stats['total_thresholds'] == 4
    assert stats['thresholds'] == [1.0, 1.25, 1.5, 1.75]
    assert stats['mond_best_threshold'] == 1.0
    assert stats['nfw_best_threshold'] == 1.75
    assert stats['mond_max_pass_rate'] == 0.8
    assert stats['nfw_max_pass_rate'] == 0.75
    assert abs(stats['mond_avg_pass_rate'] - 0.725) < 1e-6
    assert abs(stats['nfw_avg_pass_rate'] - 0.675) < 1e-6
    assert stats['crossover_point'] == 1.5  # NFW overtakes MOND at 1.5


def test_generate_summary_text():
    """Test generation of summary text."""
    stats = {
        'total_thresholds': 4,
        'thresholds': [1.0, 1.25, 1.5, 1.75],
        'mond_best_threshold': 1.0,
        'nfw_best_threshold': 1.75,
        'mond_max_pass_rate': 0.8,
        'nfw_max_pass_rate': 0.75,
        'mond_avg_pass_rate': 0.725,
        'nfw_avg_pass_rate': 0.675,
        'crossover_point': 1.5
    }

    text = generate_summary_text(stats)

    assert "SENSITIVITY ANALYSIS SUMMARY" in text
    assert "Total thresholds tested: 4" in text
    assert "MOND (Modified Newtonian Dynamics) Results:" in text
    assert "NFW (Navarro-Frenk-White) Dark Matter Halo Results:" in text
    assert "Crossover point" in text
    assert "1.50" in text


def test_write_summary():
    """Test writing summary to file."""
    summary_text = "Test summary content\nLine 2\nLine 3"

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_summary.txt"
        write_summary(summary_text, str(output_path))

        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
        assert content == summary_text