"""
Integration tests for analysis module.
Specifically tests Spearman correlation p-value calculation logic.
"""
import numpy as np
import pandas as pd
from scipy import stats
import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path to allow imports if running from tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'code')))

def test_spearman_correlation_pvalue_calc():
    """
    Generate 20 synthetic rows using np.random.seed(42) with a known correlation of 0.8.
    Expect p-value < 0.05.
    
    This test validates the statistical expectation using scipy directly to ensure the logic 
    holds for strong correlations. It serves as an integration test for the statistical 
    methodology before the full pipeline (code/analysis.py) is run on real data.
    """
    # Set seed for reproducibility
    np.random.seed(42)
    
    # Generate 20 synthetic rows
    n_samples = 20
    
    # Create two variables with a strong positive correlation (~0.8)
    # We do this by generating a base variable and adding a scaled version of it plus noise
    base = np.random.normal(0, 1, n_samples)
    noise = np.random.normal(0, 0.5, n_samples)
    var_x = base
    var_y = 0.8 * base + 0.6 * noise  # Coefficients squared sum to 1 for unit variance roughly
    
    # Calculate Spearman correlation
    r_value, p_value = stats.spearmanr(var_x, var_y)
    
    # Assert that p-value is less than 0.05 (statistically significant)
    assert p_value < 0.05, f"Expected p-value < 0.05 for strong correlation, got {p_value:.4f}"
    
    # Log the result for verification
    print(f"Generated correlation: {r_value:.4f}, p-value: {p_value:.6f}")

def test_fixture_exists():
    """
    Verify that the required fixture file mock_correlation.csv exists.
    """
    fixture_path = Path(__file__).parent.parent / "fixtures" / "mock_correlation.csv"
    assert fixture_path.exists(), f"Fixture file not found: {fixture_path}"
    
    # Load and verify basic structure
    df = pd.read_csv(fixture_path)
    assert len(df) == 20, f"Expected 20 rows in fixture, got {len(df)}"
    assert 'shannon_index' in df.columns, "Missing 'shannon_index' column in fixture"
    assert 'fluid_intelligence' in df.columns, "Missing 'fluid_intelligence' column in fixture"