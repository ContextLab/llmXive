import pytest
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import json
from pathlib import Path

# Import the function to test
# Assuming the file is code/interpret/diagnostics.py
import sys
sys.path.insert(0, 'code')
from interpret.diagnostics import diagnose_nonlinearity, generate_nonlinear_features

def test_generate_nonlinear_features():
    """Test that polynomial and interaction features are generated correctly."""
    df = pd.DataFrame({
        'x1': [1, 2, 3],
        'x2': [4, 5, 6]
    })
    
    result = generate_nonlinear_features(df, ['x1', 'x2'])
    
    assert 'x1_sq' in result.columns
    assert 'x2_sq' in result.columns
    assert 'x1_x_x2' in result.columns
    
    # Check values
    assert result['x1_sq'].iloc[0] == 1
    assert result['x1_x_x2'].iloc[0] == 4

def test_diagnose_nonlinearity_low_r2_improvement():
    """Test diagnosis when non-linear features significantly improve R2."""
    # Create a dataset where y = x1^2 + noise (non-linear)
    np.random.seed(42)
    n = 100
    x1 = np.random.rand(n)
    x2 = np.random.rand(n)
    y = x1**2 + np.random.normal(0, 0.1, n)
    
    df = pd.DataFrame({'x1': x1, 'x2': x2, 'y': y})
    X = df[['x1', 'x2']]
    y_series = df['y']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_series, test_size=0.2, random_state=42)
    
    result = diagnose_nonlinearity(X_train, y_train, X_test, y_test)
    
    # The base linear model should have low R2
    assert result['base_r2'] < 0.5
    # The expanded model should have significantly higher R2
    assert result['improvement'] > 0.15
    assert "Strong evidence" in result['conclusion']

def test_diagnose_nonlinearity_high_r2():
    """Test diagnosis when R2 is already high."""
    # Create a linear dataset
    np.random.seed(42)
    n = 100
    x1 = np.random.rand(n)
    x2 = np.random.rand(n)
    y = 2 * x1 + 3 * x2 + np.random.normal(0, 0.1, n)
    
    df = pd.DataFrame({'x1': x1, 'x2': x2, 'y': y})
    X = df[['x1', 'x2']]
    y_series = df['y']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_series, test_size=0.2, random_state=42)
    
    result = diagnose_nonlinearity(X_train, y_train, X_test, y_test)
    
    # Base model should have high R2
    assert result['base_r2'] >= 0.5
    assert "No non-linearity diagnosis" in result['conclusion']

def test_diagnose_nonlinearity_low_r2_no_improvement():
    """Test diagnosis when R2 is low and no improvement from expansion."""
    # Create a dataset with high noise or missing features
    np.random.seed(42)
    n = 100
    x1 = np.random.rand(n)
    x2 = np.random.rand(n)
    y = np.random.rand(n) # Pure noise
    
    df = pd.DataFrame({'x1': x1, 'x2': x2, 'y': y})
    X = df[['x1', 'x2']]
    y_series = df['y']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_series, test_size=0.2, random_state=42)
    
    result = diagnose_nonlinearity(X_train, y_train, X_test, y_test)
    
    assert result['base_r2'] < 0.5
    # Improvement should be small
    assert result['improvement'] < 0.05
    assert "missing critical descriptors" in result['conclusion'].lower() or "data quality" in result['conclusion'].lower()