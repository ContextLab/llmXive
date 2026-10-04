"""
Tests for T039: Visualization Generation.
Verifies that the script runs without error and produces expected files.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from visualize_results import (
    plot_fixation_distribution,
    plot_model_coefficients,
    plot_power_curve,
    load_features,
    load_lmm_results,
    load_power_analysis,
    ensure_dir
)
from config import Config

class MockConfig:
    def __init__(self, tmp_dir):
        self.PROCESSED_DATA_DIR = Path(tmp_dir) / "data" / "processed"
        self.RESULTS_DIR = Path(tmp_dir) / "results"
        self.FIGURES_DIR = Path(tmp_dir) / "results" / "figures"
        self.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        self.FIGURES_DIR.mkdir(parents=True, exist_ok=True)

@pytest.fixture
def temp_config():
    with tempfile.TemporaryDirectory() as tmp_dir:
        config = MockConfig(tmp_dir)
        yield config

def test_ensure_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        p = Path(tmp_dir) / "subdir" / "deep"
        ensure_dir(p)
        assert p.exists()
        assert p.is_dir()

def test_plot_fixation_distribution(temp_config):
    # Create dummy features
    df = pd.DataFrame({
        'fixation_ratio': np.random.rand(100) * 2,
        'participant_id': range(100)
    })
    out_path = temp_config.FIGURES_DIR / "test_fixation.png"
    
    # Mock logger
    mock_logger = MagicMock()
    
    plot_fixation_distribution(df, out_path, mock_logger)
    
    assert out_path.exists()
    assert out_path.stat().st_size > 0

def test_plot_model_coefficients(temp_config):
    # Create dummy LMM results
    df = pd.DataFrame({
        'term': ['Intercept', 'fixation_ratio', 'emotion'],
        'estimate': [2.5, 0.45, -0.1],
        'std_error': [0.1, 0.05, 0.02]
    })
    out_path = temp_config.FIGURES_DIR / "test_coeffs.png"
    mock_logger = MagicMock()
    
    plot_model_coefficients(df, out_path, mock_logger)
    
    assert out_path.exists()
    assert out_path.stat().st_size > 0

def test_plot_power_curve(temp_config):
    power_data = {
        'sample_sizes': [10, 20, 30, 40, 50, 100, 200],
        'powers': [0.2, 0.35, 0.5, 0.65, 0.75, 0.92, 0.99],
        'effect_size': 0.5,
        'alpha': 0.05
    }
    out_path = temp_config.FIGURES_DIR / "test_power.png"
    mock_logger = MagicMock()
    
    plot_power_curve(power_data, out_path, mock_logger)
    
    assert out_path.exists()
    assert out_path.stat().st_size > 0

def test_load_features_missing(temp_config):
    result = load_features(temp_config)
    assert result is None

def test_load_lmm_results_missing(temp_config):
    result = load_lmm_results(temp_config)
    assert result is None

def test_load_power_analysis_missing(temp_config):
    result = load_power_analysis(temp_config)
    assert result is None