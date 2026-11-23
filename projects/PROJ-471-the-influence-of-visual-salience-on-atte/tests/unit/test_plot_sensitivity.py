import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.plot_sensitivity import (
    load_sensitivity_results,
    load_lmm_results,
    create_sensitivity_plot,
    append_disclaimer_to_artifacts
)
from config import get_paths

@pytest.fixture
def mock_sensitivity_data():
    """Create mock sensitivity analysis data."""
    return {
        "model_a": {
            "salience_effect": 0.45,
            "ci_low": 0.32,
            "ci_high": 0.58,
            "p_value": 0.001,
            "significant": True
        },
        "model_b": {
            "salience_effect": 0.38,
            "ci_low": 0.25,
            "ci_high": 0.51,
            "p_value": 0.003,
            "significant": True
        },
        "comparison": {
            "effect_difference": 0.07,
            "stability": "stable"
        }
    }

@pytest.fixture
def mock_lmm_results():
    """Create mock LMM results DataFrame."""
    data = {
        'model': ['Model A', 'Model B'],
        'term': ['salience', 'salience'],
        'coefficient': [0.45, 0.38],
        'std_error': [0.065, 0.065],
        't_value': [6.92, 5.85],
        'p_value': [0.001, 0.003],
        'significant': [True, True]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_paths(tmp_path):
    """Create temporary directory structure for testing."""
    # Create directory structure
    interim_dir = tmp_path / "data" / "interim"
    processed_dir = tmp_path / "data" / "processed"
    figures_dir = tmp_path / "figures"
    
    interim_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    figures_dir.mkdir(parents=True)
    
    # Create mock files
    sens_file = interim_dir / "sensitivity_analysis_results.json"
    with open(sens_file, 'w') as f:
        json.dump({
            "model_a": {"salience_effect": 0.45, "ci_low": 0.32, "ci_high": 0.58, "p_value": 0.001, "significant": True},
            "model_b": {"salience_effect": 0.38, "ci_low": 0.25, "ci_high": 0.51, "p_value": 0.003, "significant": True}
        }, f)
    
    lmm_file = processed_dir / "lmm_results.csv"
    pd.DataFrame({
        'model': ['Model A', 'Model B'],
        'term': ['salience', 'salience'],
        'coefficient': [0.45, 0.38]
    }).to_csv(lmm_file, index=False)
    
    results_file = processed_dir / "results.json"
    with open(results_file, 'w') as f:
        json.dump({"model_results": "test"}, f)
    
    return {
        "interim": interim_dir,
        "processed": processed_dir,
        "figures": figures_dir,
        "temp_root": tmp_path
    }

def test_load_sensitivity_results(mock_sensitivity_data, temp_paths):
    """Test loading sensitivity results from JSON file."""
    results = load_sensitivity_results(temp_paths["interim"] / "sensitivity_analysis_results.json")
    
    assert "model_a" in results
    assert "model_b" in results
    assert results["model_a"]["salience_effect"] == 0.45
    assert results["model_b"]["significant"] is True

def test_load_lmm_results(mock_lmm_results, temp_paths):
    """Test loading LMM results from CSV file."""
    results = load_lmm_results(temp_paths["processed"] / "lmm_results.csv")
    
    assert isinstance(results, pd.DataFrame)
    assert "coefficient" in results.columns
    assert len(results) == 2

def test_create_sensitivity_plot(mock_sensitivity_data, mock_lmm_results, temp_paths):
    """Test creating sensitivity analysis plot."""
    output_path = temp_paths["figures"] / "test_plot.png"
    
    result_path = create_sensitivity_plot(
        mock_sensitivity_data,
        mock_lmm_results,
        output_path=output_path
    )
    
    assert result_path.exists()
    assert result_path.suffix == ".png"
    assert result_path.stat().st_size > 0  # File should have content

def test_append_disclaimer_to_artifacts(temp_paths):
    """Test appending disclaimers to artifacts."""
    # Create necessary files first
    sens_file = temp_paths["interim"] / "sensitivity_analysis_results.json"
    with open(sens_file, 'w') as f:
        json.dump({"test": "data"}, f)
    
    results_file = temp_paths["processed"] / "results.json"
    with open(results_file, 'w') as f:
        json.dump({"model": "A"}, f)
    
    updated = append_disclaimer_to_artifacts()
    
    # Check that files were updated
    assert any("sensitivity_analysis_results.json" in k for k in updated.keys())
    assert any("results.json" in k for k in updated.keys())
    assert any("disclaimer_log.json" in k for k in updated.keys())
    
    # Verify disclaimer was added
    with open(sens_file, 'r') as f:
        sens_data = json.load(f)
        assert "disclaimer" in sens_data
        assert "correlational" in sens_data["disclaimer"].lower()

def test_plot_with_non_significant_results(temp_paths):
    """Test plot creation with non-significant results."""
    non_sig_data = {
        "model_a": {
            "salience_effect": 0.12,
            "ci_low": -0.05,
            "ci_high": 0.29,
            "p_value": 0.18,
            "significant": False
        },
        "model_b": {
            "salience_effect": 0.09,
            "ci_low": -0.08,
            "ci_high": 0.26,
            "p_value": 0.29,
            "significant": False
        }
    }
    
    lmm_df = pd.DataFrame({
        'model': ['Model A', 'Model B'],
        'coefficient': [0.12, 0.09]
    })
    
    output_path = temp_paths["figures"] / "non_sig_plot.png"
    result_path = create_sensitivity_plot(non_sig_data, lmm_df, output_path=output_path)
    
    assert result_path.exists()
    # Verify no significance markers (stars) in the plot file would be checked visually
    # For now, just verify file creation

def test_error_handling_missing_files(temp_paths):
    """Test error handling when required files are missing."""
    with pytest.raises(FileNotFoundError):
        load_sensitivity_results(temp_paths["interim"] / "nonexistent.json")
    
    with pytest.raises(FileNotFoundError):
        load_lmm_results(temp_paths["processed"] / "nonexistent.csv")
