"""
Unit tests for the variable selection module (T015a).
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.variable_selection import (
    load_sampled_data,
    calculate_vif,
    select_variables_by_vif,
    identify_climate_columns,
    save_selected_variables,
    run_variable_selection
)


def test_identify_climate_columns():
    """Test that climate columns are correctly identified."""
    # Create a mock DataFrame with various columns
    df = pd.DataFrame({
        'species': ['A', 'B'],
        'bio1': [1.0, 2.0],
        'bio2': [1.0, 2.0],
        'bio19': [1.0, 2.0],
        'bio20': [1.0, 2.0],  # Should be ignored
        'non_climate': [1.0, 2.0],
        'BIO1': [1.0, 2.0]  # Should be included (case insensitive)
    })
    
    climate_vars = identify_climate_columns(df)
    
    # Should find bio1, bio2, bio19, and BIO1 (but not bio20)
    assert 'bio1' in climate_vars
    assert 'bio2' in climate_vars
    assert 'bio19' in climate_vars
    assert 'BIO1' in climate_vars
    assert 'bio20' not in climate_vars
    assert 'non_climate' not in climate_vars


def test_calculate_vif():
    """Test VIF calculation with known data."""
    # Create a simple DataFrame with some correlation
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'x1': np.random.randn(n),
        'x2': np.random.randn(n),
        'x3': np.random.randn(n)
    })
    
    # Add some correlation
    df['x2'] = df['x1'] * 0.5 + np.random.randn(n) * 0.5
    
    features = ['x1', 'x2', 'x3']
    vif_df = calculate_vif(df, features)
    
    assert len(vif_df) == 3
    assert 'variable' in vif_df.columns
    assert 'vif' in vif_df.columns
    
    # All VIF values should be >= 1 (no perfect multicollinearity)
    assert all(vif_df['vif'] >= 1)


def test_select_variables_by_vif():
    """Test iterative VIF selection."""
    np.random.seed(42)
    n = 200
    
    # Create correlated variables
    base = np.random.randn(n)
    df = pd.DataFrame({
        'var1': base,
        'var2': base * 0.9 + np.random.randn(n) * 0.1,  # Highly correlated
        'var3': base * 0.1 + np.random.randn(n) * 0.9,  # Less correlated
        'var4': np.random.randn(n)  # Independent
    })
    
    features = ['var1', 'var2', 'var3', 'var4']
    
    # With max_vif=5, var2 should be removed first
    selected = select_variables_by_vif(df, features, max_vif=5.0)
    
    # Should have reduced the set
    assert len(selected) < len(features)
    # var4 should definitely be kept (independent)
    assert 'var4' in selected


def test_load_sampled_data():
    """Test stratified sampling."""
    # Create a mock dataset
    data = {
        'species': ['A'] * 100 + ['B'] * 50 + ['C'] * 25,
        'value': range(175)
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    
    try:
        # Sample 30 points
        sampled = load_sampled_data(temp_path, sample_size=30, seed=42)
        
        # Check total count
        assert len(sampled) == 30
        
        # Check that all species are represented (proportional)
        assert 'A' in sampled['species'].values
        assert 'B' in sampled['species'].values
        assert 'C' in sampled['species'].values
    finally:
        os.unlink(temp_path)


def test_save_selected_variables():
    """Test saving selected variables to JSON."""
    selected = ['bio1', 'bio2', 'bio12']
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name
    
    try:
        save_selected_variables(selected, output_path)
        
        # Verify file was created and contains correct data
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['selected_variables'] == selected
        assert data['count'] == len(selected)
        assert 'timestamp' in data
        assert data['threshold'] == 5.0
    finally:
        os.unlink(output_path)


def test_run_variable_selection_end_to_end():
    """Test the full pipeline with mock data."""
    np.random.seed(42)
    n = 500
    
    # Create mock data with climate variables
    data = {
        'species': ['A'] * 200 + ['B'] * 200 + ['C'] * 100,
        'bio1': np.random.randn(n),
        'bio2': np.random.randn(n),
        'bio3': np.random.randn(n),
        'bio4': np.random.randn(n),
        'bio5': np.random.randn(n),
        'bio6': np.random.randn(n),
        'bio7': np.random.randn(n),
        'bio8': np.random.randn(n),
        'bio9': np.random.randn(n),
        'bio10': np.random.randn(n),
        'bio11': np.random.randn(n),
        'bio12': np.random.randn(n),
        'bio13': np.random.randn(n),
        'bio14': np.random.randn(n),
        'bio15': np.random.randn(n),
        'bio16': np.random.randn(n),
        'bio17': np.random.randn(n),
        'bio18': np.random.randn(n),
        'bio19': np.random.randn(n),
    }
    
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f_in:
        df.to_csv(f_in.name, index=False)
        input_path = f_in.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f_out:
        output_path = f_out.name
    
    try:
        result = run_variable_selection(
            input_path=input_path,
            output_path=output_path,
            sample_size=100,
            seed=42,
            max_vif=5.0
        )
        
        # Verify result is a list of strings
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(v, str) for v in result)
        
        # Verify output file was created
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['selected_variables'] == result
    finally:
        os.unlink(input_path)
        os.unlink(output_path)
