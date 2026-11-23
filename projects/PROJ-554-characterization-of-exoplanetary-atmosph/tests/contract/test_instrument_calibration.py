import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json

from instrument_calibration import (
    load_metadata,
    load_retrieval_results,
    bin_temperature,
    analyze_instrument_bias,
    generate_report_md
)

def test_bin_temperature():
    """Test temperature binning logic."""
    temps = pd.Series([500, 1200, 1700, 2500])
    bins = bin_temperature(temps)
    expected_labels = ['<1000K', '1000-1500K', '1500-2000K', '>2000K']
    assert list(bins) == expected_labels

def test_analyze_instrument_bias_basic():
    """Test basic bias analysis with synthetic data."""
    # Create mock metadata
    metadata_df = pd.DataFrame({
        'planet_name': ['p1', 'p2', 'p3', 'p4'],
        'temperature': [800, 1200, 1800, 2200],
        'instrument': ['HST', 'HST', 'Spitzer', 'Spitzer']
    })

    # Create mock retrieval results
    # p1, p2, p3, p4 have water mixing ratios
    retrieval_df = pd.DataFrame({
        'planet_name': ['p1', 'p2', 'p3', 'p4'],
        'water_mixing_ratio': [-4.0, -4.1, -3.0, -3.1], # HST ~ -4, Spitzer ~ -3
        'is_upper_limit': [False, False, False, False]
    })

    analysis, flags = analyze_instrument_bias(metadata_df, retrieval_df)

    assert 'HST' in analysis
    assert 'Spitzer' in analysis
    assert analysis['HST']['count'] == 2
    assert analysis['Spitzer']['count'] == 2

    # Check for bias flag (difference between -4 and -3 is 1.0 dex, > 0.5 threshold)
    assert len(flags) > 0
    assert any("HST" in f or "Spitzer" in f for f in flags)

def test_analyze_instrument_bias_with_upper_limits():
    """Test that upper limits are counted but not used for mean/std calculation."""
    metadata_df = pd.DataFrame({
        'planet_name': ['p1', 'p2'],
        'temperature': [1000, 1000],
        'instrument': ['HST', 'HST']
    })

    retrieval_df = pd.DataFrame({
        'planet_name': ['p1', 'p2'],
        'water_mixing_ratio': [-4.0, -99.0], # -99 is a placeholder for upper limit
        'is_upper_limit': [False, True]
    })

    analysis, flags = analyze_instrument_bias(metadata_df, retrieval_df)

    assert analysis['HST']['count'] == 1 # Only detected
    assert analysis['HST']['upper_limit_count'] == 1

def test_generate_report_md_creates_file(tmp_path):
    """Test that report generation creates a valid markdown file."""
    output_file = tmp_path / "test_report.md"
    analysis = {
        'HST': {
            'count': 2,
            'mean_water_abundance': -4.0,
            'std_water_abundance': 0.1,
            'median_water_abundance': -4.0,
            'temp_bin_breakdown': {'1000-1500K': {'count': 2, 'mean': -4.0, 'std': 0.1}},
            'upper_limit_count': 0
        }
    }
    flags = ['Instrument HST shows high variance']

    generate_report_md(analysis, flags, str(output_file))

    assert output_file.exists()
    content = output_file.read_text()
    assert "Instrument-Specific Calibration Validation Report" in content
    assert "HST" in content
    assert "Systematic Error Flags" in content