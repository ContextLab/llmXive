import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Mock the config to avoid path issues in tests
from unittest.mock import patch, MagicMock

from code.generate_diagnostic_plots import (
    create_residuals_plot,
    create_qq_plot,
    create_scale_location_plot,
    create_residuals_leverage_plot,
    generate_all_plots
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)

def test_create_residuals_plot(temp_dir):
    """Test that residuals plot is created successfully."""
    residuals = np.random.normal(0, 1, 100)
    fitted = np.random.normal(0, 1, 100)
    output_path = Path(temp_dir) / "test_residuals.png"
    
    create_residuals_plot(residuals, fitted, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_create_qq_plot(temp_dir):
    """Test that Q-Q plot is created successfully."""
    residuals = np.random.normal(0, 1, 100)
    output_path = Path(temp_dir) / "test_qq.png"
    
    create_qq_plot(residuals, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_create_scale_location_plot(temp_dir):
    """Test that scale-location plot is created successfully."""
    residuals = np.random.normal(0, 1, 100)
    fitted = np.random.normal(0, 1, 100)
    output_path = Path(temp_dir) / "test_scale.png"
    
    create_scale_location_plot(residuals, fitted, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_create_residuals_leverage_plot(temp_dir):
    """Test that residuals vs leverage plot is created successfully."""
    residuals = np.random.normal(0, 1, 100)
    leverage = np.random.beta(2, 2, 100) # Leverage is usually between 0 and 1
    output_path = Path(temp_dir) / "test_leverage.png"
    
    create_residuals_leverage_plot(residuals, leverage, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0