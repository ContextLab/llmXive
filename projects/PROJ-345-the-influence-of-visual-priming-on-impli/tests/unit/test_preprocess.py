import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocess import check_confounding

class TestConfoundingCheck:
    """Unit tests for the confounding check functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a simple dataset with no confounding
        np.random.seed(42)
        n_trials = 100
        
        self.df_no_confound = pd.DataFrame({
            'trial_id': range(n_trials),
            'prime_condition': np.random.choice(['A', 'B'], n_trials),
            'response_time': np.random.normal(500, 100, n_trials)
        })
        
        # Create a dataset with clear confounding
        self.df_confound = pd.DataFrame({
            'trial_id': range(100),
            'prime_condition': ['A'] * 50 + ['B'] * 50,  # All A first, then all B
            'response_time': np.random.normal(500, 100, 100)
        })

    def test_no_confounding(self):
        """Test that no confounding is detected when conditions are randomized."""
        report = check_confounding(self.df_no_confound)
        
        assert "error" not in report
        assert report["conclusion"] == "No significant confounding detected"
        assert report["correlation_with_order"]["is_significant"] == False
        assert abs(report["correlation_with_order"]["pearson_r"]) < 0.3  # Low correlation expected

    def test_confounding_detected(self):
        """Test that confounding is detected when conditions are not randomized."""
        report = check_confounding(self.df_confound)
        
        assert "error" not in report
        assert report["conclusion"] == "Confounding detected"
        assert report["correlation_with_order"]["is_significant"] == True
        # High correlation expected due to sequential arrangement
        assert abs(report["correlation_with_order"]["pearson_r"]) > 0.5

    def test_missing_columns(self):
        """Test handling of missing required columns."""
        df_missing = pd.DataFrame({
            'trial_id': range(10),
            'response_time': np.random.normal(500, 100, 10)
        })
        
        report = check_confounding(df_missing)
        
        assert "error" in report
        assert "Prime condition column not found" in report["error"]

    def test_output_file_generation(self, tmp_path):
        """Test that the confounding report is saved to a JSON file."""
        output_file = tmp_path / "confounding_report.json"
        
        report = check_confounding(
            self.df_no_confound, 
            output_path=str(output_file)
        )
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report["analysis_type"] == "confounding_check"
        assert "correlation_with_order" in saved_report
        assert "conclusion" in saved_report

    def test_block_confounding_check(self):
        """Test block confounding detection when block_id is present."""
        df_with_blocks = pd.DataFrame({
            'trial_id': range(200),
            'prime_condition': ['A'] * 100 + ['B'] * 100,
            'block_id': ['block1'] * 50 + ['block2'] * 50 + ['block1'] * 50 + ['block2'] * 50,
            'response_time': np.random.normal(500, 100, 200)
        })
        
        report = check_confounding(df_with_blocks)
        
        assert "error" not in report
        assert "block_confounding" in report
        assert report["block_confounding"] is not None
        assert "is_balanced" in report["block_confounding"]

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        df_empty = pd.DataFrame(columns=['trial_id', 'prime_condition'])
        
        report = check_confounding(df_empty)
        
        assert "error" in report
        assert "No data provided" in report["error"]