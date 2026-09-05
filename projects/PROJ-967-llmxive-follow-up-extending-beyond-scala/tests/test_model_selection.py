"""
Unit tests for model selection functions in model_selection.py
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import tempfile

# Ensure we can import from code/
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.model_selection import select_model_type, save_selection

def test_select_model_type_insufficient_data():
    """Test model selection with insufficient data (N < 30)."""
    n_samples = 20
    model_type, reason = select_model_type(n_samples)
    
    assert model_type == "fail"
    assert "N < 30" in reason

def test_select_model_type_low_power():
    """Test model selection with low power (30 <= N < 300)."""
    n_samples = 150
    model_type, reason = select_model_type(n_samples)
    
    assert model_type == "ridge"
    assert "low_power" in reason

def test_select_model_type_high_power():
    """Test model selection with high power (N >= 300)."""
    n_samples = 500
    model_type, reason = select_model_type(n_samples)
    
    assert model_type == "rf"
    assert "high_power" in reason

def test_save_selection(tmp_path):
    """Test saving model selection results."""
    output_path = tmp_path / "model_selection.json"
    
    save_selection(
        output_path=str(output_path),
        model_type="ridge",
        n_samples=150,
        threshold=30,
        reason="low_power"
    )
    
    # Check that file was created
    assert output_path.exists()
    
    # Check content
    import json
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data['model_type'] == "ridge"
    assert data['n_samples'] == 150
    assert data['threshold'] == 30
    assert data['reason'] == "low_power"