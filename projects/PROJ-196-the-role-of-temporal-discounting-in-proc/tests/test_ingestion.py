"""
Unit tests for code/ingestion.py functions.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add parent directory to path to allow imports if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the module under test
from code.ingestion import (
    generate_delay_discounting_data,
    generate_procrastination_data,
    generate_nback_data,
    validate_dgp_config,
    calculate_cronbach_alpha,
    harmonize_datasets,
    DEFAULT_DGP_CONFIG
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_generate_delay_discounting_data(temp_dir):
    """Test generation of delay discounting data."""
    output_path = os.path.join(temp_dir, "delay_discounting.csv")
    
    # Generate data
    df = generate_delay_discounting_data(
        n_participants=50,
        output_path=output_path,
        seed=42
    )
    
    # Check file was created
    assert os.path.exists(output_path)
    
    # Check dataframe structure
    assert 'participant_id' in df.columns
    assert 'delay' in df.columns
    assert 'indifference_point' in df.columns
    assert len(df) == 50 * 5  # 50 participants * 5 delays

def test_generate_procrastination_data(temp_dir):
    """Test generation of procrastination data."""
    output_path = os.path.join(temp_dir, "procrastination.csv")
    
    # Generate data
    df = generate_procrastination_data(
        n_participants=50,
        output_path=output_path,
        seed=42
    )
    
    # Check file was created
    assert os.path.exists(output_path)
    
    # Check dataframe structure
    assert 'participant_id' in df.columns
    assert 'procrastination_score' in df.columns
    # Check for item columns
    item_cols = [c for c in df.columns if c.startswith('item_')]
    assert len(item_cols) == DEFAULT_DGP_CONFIG["procrastination"]["n_items"]
    assert len(df) == 50

def test_generate_nback_data(temp_dir):
    """Test generation of n-back task data."""
    output_path = os.path.join(temp_dir, "nback.csv")
    
    # Generate data
    df = generate_nback_data(
        n_participants=50,
        output_path=output_path,
        seed=42
    )
    
    # Check file was created
    assert os.path.exists(output_path)
    
    # Check dataframe structure
    assert 'participant_id' in df.columns
    assert 'wm_accuracy' in df.columns
    assert 'wm_rt' in df.columns
    assert len(df) == 50

def test_validate_dgp_config_valid():
    """Test that valid config passes."""
    assert validate_dgp_config(DEFAULT_DGP_CONFIG) is True

def test_validate_dgp_config_invalid_missing_section():
    """Test that invalid config raises SystemExit."""
    invalid_config = DEFAULT_DGP_CONFIG.copy()
    del invalid_config["n_participants"]
    
    with pytest.raises(SystemExit) as exc_info:
        validate_dgp_config(invalid_config)
    assert exc_info.value.code == 1

def test_calculate_cronbach_alpha():
    """Test Cronbach's alpha calculation."""
    # Create sample data with known reliability
    np.random.seed(42)
    n_items = 10
    n_participants = 100
    
    # Generate correlated items (high alpha expected)
    common_factor = np.random.normal(0, 1, n_participants)
    data = np.zeros((n_participants, n_items))
    for i in range(n_items):
        data[:, i] = common_factor + np.random.normal(0, 0.5, n_participants)
    
    alpha = calculate_cronbach_alpha(data)
    
    # High alpha expected for correlated items
    assert alpha > 0.7
    assert alpha <= 1.0

def test_calculate_cronbach_alpha_low_reliability():
    """Test Cronbach's alpha with uncorrelated items."""
    np.random.seed(42)
    n_items = 10
    n_participants = 100
    
    # Generate uncorrelated items (low alpha expected)
    data = np.random.normal(0, 1, (n_participants, n_items))
    
    alpha = calculate_cronbach_alpha(data)
    
    # Alpha should be low (close to 0)
    assert alpha < 0.5

def test_harmonize_datasets(temp_dir):
    """Test harmonization of multiple datasets."""
    # Generate individual datasets
    dd_path = os.path.join(temp_dir, "delay_discounting.csv")
    proc_path = os.path.join(temp_dir, "procrastination.csv")
    nback_path = os.path.join(temp_dir, "nback.csv")
    
    generate_delay_discounting_data(50, dd_path, 42)
    generate_procrastination_data(50, proc_path, 42)
    generate_nback_data(50, nback_path, 42)
    
    # Harmonize
    df = harmonize_datasets(dd_path, proc_path, nback_path)
    
    # Check merged dataframe
    assert 'participant_id' in df.columns
    assert 'discount_rate_k' in df.columns
    assert 'procrastination_score' in df.columns
    assert 'wm_accuracy' in df.columns
    assert 'wm_rt' in df.columns
    assert len(df) == 50  # All participants matched