import os
import sys
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(code_dir))

from generate_stability_report import load_results_metrics, generate_stability_report, save_report

class TestStabilityReport:
    
    def test_generate_stability_from_raw_sensitivity(self, tmp_path):
        """Test generation of report from raw sensitivity shift data."""
        # Create mock raw sensitivity data (as if from T032/T034)
        data = {
            'comparison': ['Immediate vs Delayed'] * 10,
            'shift': range(10),
            'p_value': [0.04, 0.05, 0.03, 0.06, 0.04, 0.02, 0.05, 0.04, 0.03, 0.01],
            'significant': [True, False, True, False, True, True, False, True, True, True], # 7 True
            'conclusion_change': [0, 1, 0, 1, 0, 0, 1, 0, 0, 0] # 3 flips
        }
        df = pd.DataFrame(data)
        
        # Mock the input file path
        input_file = tmp_path / "results_metrics.csv"
        df.to_csv(input_file, index=False)
        
        # Patch the function to use our temp file
        original_func = load_results_metrics
        def mock_load():
            return pd.read_csv(input_file)
        
        # Temporarily replace
        import generate_stability_report as mod
        mod.load_results_metrics = mock_load
        
        try:
            result_df = generate_stability_report(df)
            
            # Verify stability: 7/10 = 0.7
            stability_row = result_df[result_df['metric_name'] == 'significance_stability']
            assert len(stability_row) == 1
            assert abs(stability_row['value'].iloc[0] - 0.7) < 1e-6
            
            # Verify flip rate: 3/10 = 0.3
            flip_row = result_df[result_df['metric_name'] == 'significance_flip_rate']
            assert len(flip_row) == 1
            assert abs(flip_row['value'].iloc[0] - 0.3) < 1e-6
            
        finally:
            mod.load_results_metrics = original_func

    def test_generate_stability_from_aggregated(self, tmp_path):
        """Test generation when input is already aggregated."""
        data = {
            'significance_stability': [0.85],
            'significance_flip_rate': [0.15]
        }
        df = pd.DataFrame(data)
        
        input_file = tmp_path / "results_metrics.csv"
        df.to_csv(input_file, index=False)
        
        import generate_stability_report as mod
        mod.load_results_metrics = lambda: pd.read_csv(input_file)
        
        try:
            result_df = generate_stability_report(df)
            
            # Should preserve values
            assert 'significance_stability' in result_df.columns or 'metric_name' in result_df.columns
            
        finally:
            mod.load_results_metrics = original_func

    def test_save_report_creates_file(self, tmp_path):
        """Test that save_report writes the file correctly."""
        data = {
            'metric_name': ['test_metric'],
            'value': [0.99],
            'description': ['Test description']
        }
        df = pd.DataFrame(data)
        
        output_path = save_report(df)
        
        assert os.path.exists(output_path)
        loaded = pd.read_csv(output_path)
        assert len(loaded) == 1
        assert loaded['value'].iloc[0] == 0.99