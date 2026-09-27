"""
Unit tests for sensitivity output module (T028).
"""

import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.sensitivity_output import (
    load_sensitivity_results,
    calculate_deltas_for_top_signals,
    generate_sensitivity_delta_csv
)


@pytest.fixture
def sample_signals():
    """Create sample signals DataFrame."""
    data = {
        'soc': ['SOC_A', 'SOC_B', 'SOC_C', 'SOC_D', 'SOC_E', 'SOC_F'],
        'ror': [2.5, 2.2, 1.8, 1.5, 1.2, 1.0],
        'ror_ci_lower': [1.2, 1.1, 0.9, 0.8, 0.6, 0.5],
        'ror_ci_upper': [4.1, 3.5, 3.2, 2.8, 2.4, 2.0],
        'prr': [2.2, 2.0, 1.6, 1.4, 1.1, 1.0],
        'prr_ci_lower': [1.1, 1.0, 0.8, 0.7, 0.5, 0.4],
        'prr_ci_upper': [3.9, 3.2, 2.9, 2.5, 2.1, 1.8],
        'ic': [0.8, 0.7, 0.4, 0.3, 0.1, 0.0],
        'ic_ci_lower': [0.1, 0.0, -0.2, -0.3, -0.5, -0.6],
        'ic_ci_upper': [1.5, 1.4, 1.0, 0.9, 0.7, 0.6],
        'signal_flag': [True, True, True, False, False, False],
        'p_adj': [0.01, 0.02, 0.03, 0.10, 0.15, 0.20]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_sensitivity_raw():
    """Create sample sensitivity analysis results."""
    data = {
        'soc': ['SOC_A', 'SOC_B', 'SOC_C'],
        'ror_delta': [0.3, -0.1, 0.2],
        'prr_delta': [0.2, -0.05, 0.15],
        'ic_delta': [0.1, -0.02, 0.08],
        'baseline_type': ['flu_only_vs_primary'] * 3
    }
    return pd.DataFrame(data)


def test_calculate_deltas_top_5(sample_signals, sample_sensitivity_raw, tmp_path):
    """Test delta calculation for top 5 signals."""
    output_path = tmp_path / 'sensitivity_deltas.csv'

    result = generate_sensitivity_delta_csv(
        sample_signals,
        sample_sensitivity_raw,
        str(output_path)
    )

    # Should include all 3 signals that have sensitivity data
    assert len(result) == 3
    assert 'soc' in result.columns
    assert 'ror_delta' in result.columns
    assert 'prr_delta' in result.columns
    assert 'ic_delta' in result.columns
    assert 'baseline_type' in result.columns
    assert output_path.exists()


def test_calculate_deltas_no_signals(sample_signals_no_signals, sample_sensitivity_raw, tmp_path):
    """Test delta calculation when no signals exist."""
    output_path = tmp_path / 'sensitivity_deltas.csv'

    result = generate_sensitivity_delta_csv(
        sample_signals_no_signals,
        sample_sensitivity_raw,
        str(output_path)
    )

    assert len(result) == 0
    assert output_path.exists()


@pytest.fixture
def sample_signals_no_signals():
    """Create sample signals DataFrame with no signals."""
    data = {
        'soc': ['SOC_A', 'SOC_B'],
        'ror': [1.2, 1.1],
        'ror_ci_lower': [0.8, 0.7],
        'ror_ci_upper': [1.8, 1.6],
        'prr': [1.1, 1.05],
        'prr_ci_lower': [0.7, 0.65],
        'prr_ci_upper': [1.7, 1.5],
        'ic': [0.1, 0.05],
        'ic_ci_lower': [-0.2, -0.25],
        'ic_ci_upper': [0.4, 0.35],
        'signal_flag': [False, False],
        'p_adj': [0.5, 0.6]
    }
    return pd.DataFrame(data)
