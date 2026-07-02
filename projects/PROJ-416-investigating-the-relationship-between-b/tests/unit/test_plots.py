"""
Unit tests for code/analysis/plots.py.
Ensures scatter plots and residual diagnostics are generated without error.
"""
import os
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib
# Use non-interactive backend for CI/headless environments
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Import the module under test. 
# Since the API surface didn't list plots.py, we define the implementation 
# in this same task to ensure the import works and the tests pass.
# The task requires testing plots.py, so we must ensure plots.py exists and works.

# We will import the module after ensuring it exists in the codebase.
# For the purpose of this artifact, we assume code/analysis/plots.py is created 
# in a companion artifact or already exists. Since the API surface was empty for it,
# we must create it to satisfy the "real code" constraint of the task.
# However, the prompt asks for T027 which is the TEST. 
# To make the test runnable and valid, we must ensure the code being tested exists.
# The constraints say: "If a name does not exist there, either add it to the 
# appropriate file in this task's artifacts list or use a different name".
# So I will include the implementation of plots.py in the artifacts as well,
# because the test cannot run without it, and it's the only way to satisfy 
# "generate without error" on real execution.

import sys
import importlib.util

# Dynamically load code/analysis/plots.py if it exists, or handle the import
# Since I am generating the file, I will assume it is at code/analysis/plots.py
spec = importlib.util.spec_from_file_location("plots", "code/analysis/plots.py")
plots_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plots_module)

@pytest.fixture
def sample_data():
    """Create a temporary CSV with dummy statistical results for testing."""
    data = {
        'subject_id': [f'S0{i}' for i in range(1, 11)],
        'pre_treatment_score': [15.0, 18.0, 12.0, 20.0, 14.0, 16.0, 19.0, 13.0, 17.0, 21.0],
        'post_treatment_score': [10.0, 12.0, 8.0, 14.0, 9.0, 11.0, 13.0, 7.0, 11.0, 15.0],
        'global_efficiency': [0.35, 0.38, 0.32, 0.40, 0.34, 0.36, 0.39, 0.33, 0.37, 0.41],
        'modularity': [0.45, 0.42, 0.48, 0.40, 0.46, 0.44, 0.41, 0.47, 0.43, 0.39]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for plot outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_generate_scatter_plot_no_error(sample_data, temp_output_dir):
    """
    Test that generate_scatter_plot runs without raising an exception
    and creates a file on disk.
    """
    output_path = temp_output_dir / "scatter_pre_vs_post.png"
    
    # Call the function
    plots_module.generate_scatter_plot(
        sample_data, 
        x_col='pre_treatment_score', 
        y_col='post_treatment_score', 
        title='Pre vs Post Treatment',
        output_path=str(output_path)
    )
    
    # Verify file exists and has content
    assert output_path.exists(), "Scatter plot file was not created."
    assert output_path.stat().st_size > 0, "Scatter plot file is empty."

def test_generate_residual_plot_no_error(sample_data, temp_output_dir):
    """
    Test that generate_residual_plot runs without raising an exception
    and creates a file on disk.
    """
    output_path = temp_output_dir / "residuals.png"
    
    # Call the function
    plots_module.generate_residual_plot(
        sample_data, 
        x_col='pre_treatment_score', 
        y_col='post_treatment_score', 
        title='Residual Diagnostics',
        output_path=str(output_path)
    )
    
    # Verify file exists and has content
    assert output_path.exists(), "Residual plot file was not created."
    assert output_path.stat().st_size > 0, "Residual plot file is empty."

def test_generate_regression_line_plot_no_error(sample_data, temp_output_dir):
    """
    Test that generate_regression_line_plot runs without error.
    """
    output_path = temp_output_dir / "regression_line.png"
    
    plots_module.generate_regression_line_plot(
        sample_data,
        x_col='global_efficiency',
        y_col='post_treatment_score',
        title='Efficiency vs Post Score',
        output_path=str(output_path)
    )
    
    assert output_path.exists(), "Regression line plot file was not created."
    assert output_path.stat().st_size > 0, "Regression line plot file is empty."
