import os
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

from data_models import RetrievalResult
from retrieval_output import process_retrieval_results
from retrieval_output_schema import get_schema_columns

def test_process_retrieval_results_creates_csv():
    """Test that process_retrieval_results creates a valid CSV file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "results.csv")
        
        results = [
            RetrievalResult(
                planet_name="Test Planet",
                equilibrium_temp=1000.0,
                water_mixing_ratio=1e-4,
                uncertainty=1e-5,
                is_censored=False,
                snr=50.0,
                resolution=100000,
                convergence_status="converged"
            )
        ]
        
        result_path = process_retrieval_results(results, output_path)
        
        assert os.path.exists(result_path)
        
        df = pd.read_csv(result_path)
        assert len(df) == 1
        assert df.iloc[0]['planet_name'] == "Test Planet"
        assert 'log10_water_abundance' in df.columns

def test_process_retrieval_results_empty_list():
    """Test that an empty list creates an empty CSV with headers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "empty_results.csv")
        
        result_path = process_retrieval_results([], output_path)
        
        assert os.path.exists(result_path)
        
        df = pd.read_csv(result_path)
        expected_cols = get_schema_columns()
        assert list(df.columns) == expected_cols
        assert len(df) == 0

def test_process_retrieval_results_censored_data():
    """Test handling of censored (upper limit) data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "censored_results.csv")
        
        results = [
            RetrievalResult(
                planet_name="Upper Limit Planet",
                equilibrium_temp=500.0,
                water_mixing_ratio=1e-6,
                uncertainty=5e-7,
                is_censored=True,
                snr=10.0,
                resolution=30000,
                convergence_status="upper_limit"
            )
        ]
        
        result_path = process_retrieval_results(results, output_path)
        
        df = pd.read_csv(result_path)
        assert len(df) == 1
        assert df.iloc[0]['is_censored'] == True
        assert df.iloc[0]['convergence_status'] == 'upper_limit'