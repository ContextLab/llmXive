import os
import sys
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from visualization import (
    generate_scatter_with_fit,
    generate_partial_dependence_plots,
    load_processed_data,
    load_model_artifact
)

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    np.random.seed(42)
    n = 100
    data = {
        'phosphorus': np.random.normal(10, 2, n),
        'nitrogen': np.random.normal(50, 10, n),
        'root_length': np.random.normal(100, 20, n),
        'branching_density': np.random.normal(5, 1, n),
        'surface_area': np.random.normal(50, 10, n)
    }
    # Add some NaNs to test filtering
    data['phosphorus'][0] = np.nan
    return pd.DataFrame(data)

@pytest.fixture
def sample_model_artifact():
    """Create a sample model artifact dict."""
    return {
        'lmm': {'adjusted_r_squared': 0.45},
        'rf': {'r_squared': 0.42},
        'metadata': {'version': '1.0'}
    }

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_generate_scatter_with_fit(sample_dataframe, temp_output_dir):
    """Test that scatter plot generation creates a file."""
    output_path = temp_output_dir / "test_scatter.png"
    
    generate_scatter_with_fit(
        df=sample_dataframe,
        x_col='phosphorus',
        y_col='root_length',
        title="Test Plot",
        xlabel="Phosphorus",
        ylabel="Root Length",
        output_path=output_path
    )
    
    assert output_path.exists(), "Scatter plot file was not created"
    assert output_path.stat().st_size > 0, "Scatter plot file is empty"

def test_generate_partial_dependence_plots(sample_dataframe, sample_model_artifact, temp_output_dir):
    """Test that PDP generation creates expected files."""
    generate_partial_dependence_plots(
        df=sample_dataframe,
        model_artifact=sample_model_artifact,
        config={},
        output_dir=temp_output_dir
    )
    
    expected_files = [
        "pdp_phosphorus_vs_root_length.png",
        "pdp_phosphorus_vs_branching_density.png",
        "pdp_phosphorus_vs_surface_area.png",
        "pdp_nitrogen_vs_root_length.png",
        "pdp_nitrogen_vs_branching_density.png",
        "pdp_nitrogen_vs_surface_area.png"
    ]
    
    for fname in expected_files:
        fpath = temp_output_dir / fname
        assert fpath.exists(), f"Expected plot {fname} was not created"
        assert fpath.stat().st_size > 0, f"Expected plot {fname} is empty"

def test_load_processed_data_missing_file():
    """Test that load_processed_data raises error for missing file."""
    config = {'PROCESSED_DATA_PATH': '/nonexistent/path/data.csv'}
    with pytest.raises(FileNotFoundError):
        load_processed_data(config)

def test_load_model_artifact_missing_file():
    """Test that load_model_artifact raises error for missing file."""
    config = {'MODEL_METRICS_PATH': '/nonexistent/path/model.json'}
    with pytest.raises(FileNotFoundError):
        load_model_artifact(config)