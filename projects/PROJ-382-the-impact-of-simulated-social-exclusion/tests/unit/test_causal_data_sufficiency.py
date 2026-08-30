import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis import check_causal_data_sufficiency, run_meta_analysis

class TestCausalDataSufficiency:
    
    def test_sufficient_causal_data(self):
        """
        Test that when there are >= 3 causal datasets, the check passes.
        """
        # Mock results for 3 studies
        mock_results = [
            {"model_results": {"zero_inflation": {"coefficients": {"condition": -0.5}}}},
            {"model_results": {"zero_inflation": {"coefficients": {"condition": -0.6}}}},
            {"model_results": {"zero_inflation": {"coefficients": {"condition": -0.4}}}}
        ]
        
        report = check_causal_data_sufficiency(mock_results, threshold=3)
        
        assert report["is_sufficient"] is True
        assert report["n_causal_studies"] == 3
        assert "Sufficient causal data" in report["status"]
        assert report["action"] == "Proceed with Causal Meta-Analysis"

    def test_insufficient_causal_data(self):
        """
        Test that when there are < 3 causal datasets, the check reports insufficient.
        """
        # Mock results for 2 studies
        mock_results = [
            {"model_results": {"zero_inflation": {"coefficients": {"condition": -0.5}}}},
            {"model_results": {"zero_inflation": {"coefficients": {"condition": -0.6}}}}
        ]
        
        report = check_causal_data_sufficiency(mock_results, threshold=3)
        
        assert report["is_sufficient"] is False
        assert report["n_causal_studies"] == 2
        assert "Insufficient causal data" in report["status"]
        assert report["action"] == "Continue with Associational Pool"

    def test_no_causal_data(self):
        """
        Test that when there are 0 causal datasets, the check reports insufficient.
        """
        mock_results = []
        
        report = check_causal_data_sufficiency(mock_results, threshold=3)
        
        assert report["is_sufficient"] is False
        assert report["n_causal_studies"] == 0
        assert "Insufficient causal data" in report["status"]

    def test_writes_status_file(self):
        """
        Test that the status file is written to the correct location.
        """
        mock_results = [
            {"model_results": {"zero_inflation": {"coefficients": {"condition": -0.5}}}},
            {"model_results": {"zero_inflation": {"coefficients": {"condition": -0.6}}}}
        ]
        
        # This will write to the project's processed directory
        # We assume the directory structure is set up by T001a
        report = check_causal_data_sufficiency(mock_results, threshold=3)
        
        # Verify the file exists
        from config import get_project_paths
        paths = get_project_paths()
        status_file = paths["processed"] / "causal_data_sufficiency.json"
        
        assert status_file.exists(), f"Status file not found at {status_file}"
        
        with open(status_file, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report["is_sufficient"] is False
        assert saved_report["n_causal_studies"] == 2