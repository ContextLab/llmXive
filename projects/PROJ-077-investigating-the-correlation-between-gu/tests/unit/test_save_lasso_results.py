import os
import sys
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import tempfile
import pickle

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from save_lasso_results import save_lasso_results, load_lasso_results_from_analysis

def test_save_lasso_results_creates_file():
    """Test that save_lasso_results creates the expected CSV file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_lasso_results.csv")
        
        # Create dummy data
        coefficients = pd.Series({
            "TaxaA": 0.5,
            "TaxaB": 0.0,
            "TaxaC": -0.2
        })
        non_zero_count = 2
        metrics = {"r2": 0.75, "mse": 0.1}
        
        save_lasso_results(coefficients, non_zero_count, metrics, output_path)
        
        assert os.path.exists(output_path)
        
        df = pd.read_csv(output_path)
        assert "feature" in df.columns
        assert "type" in df.columns
        assert "value" in df.columns
        
        # Check for non-zero features count
        assert df[(df["feature"] == "non_zero_features") & (df["type"] == "metric")]["value"].iloc[0] == 2.0

def test_save_lasso_results_includes_metrics():
    """Test that metrics are saved correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_lasso_results.csv")
        
        coefficients = pd.Series({"TaxaA": 0.1})
        non_zero_count = 1
        metrics = {"r2": 0.9, "mse": 0.05}
        
        save_lasso_results(coefficients, non_zero_count, metrics, output_path)
        
        df = pd.read_csv(output_path)
        
        assert df[(df["feature"] == "r2")]["value"].iloc[0] == 0.9
        assert df[(df["feature"] == "mse")]["value"].iloc[0] == 0.05