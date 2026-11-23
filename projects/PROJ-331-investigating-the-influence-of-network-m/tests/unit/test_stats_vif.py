import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from stats import check_vif_and_select_method, load_subject_metrics_data

class TestVIFCheck:
    
    @pytest.fixture
    def mock_metrics_df(self):
        """Create a mock DataFrame with network_density and motif columns."""
        # Create data with some variance
        n = 50
        np.random.seed(42)
        data = {
            'subject_id': [f'sub_{i:03d}' for i in range(n)],
            'network_density': np.random.uniform(0.1, 0.3, n),
            'motif_1': np.random.uniform(-1, 1, n),
            'motif_2': np.random.uniform(-1, 1, n),
            'rsfc_strength': np.random.uniform(-1, 1, n)
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def mock_zero_var_df(self):
        """Create a mock DataFrame with constant network_density."""
        n = 50
        data = {
            'subject_id': [f'sub_{i:03d}' for i in range(n)],
            'network_density': np.ones(n) * 0.2, # Constant
            'motif_1': np.random.uniform(-1, 1, n),
            'motif_2': np.random.uniform(-1, 1, n),
            'rsfc_strength': np.random.uniform(-1, 1, n)
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def mock_high_collinear_df(self):
        """Create a mock DataFrame with high collinearity (VIF > 5)."""
        n = 50
        np.random.seed(42)
        base = np.random.uniform(0, 1, n)
        data = {
            'subject_id': [f'sub_{i:03d}' for i in range(n)],
            'network_density': base,
            'motif_1': base + np.random.normal(0, 0.01, n), # Highly correlated
            'motif_2': np.random.uniform(-1, 1, n),
            'rsfc_strength': np.random.uniform(-1, 1, n)
        }
        return pd.DataFrame(data)

    def test_normal_vif_uses_pearson(self, mock_metrics_df):
        """Test that normal variance and low VIF selects Pearson."""
        flags = check_vif_and_select_method(mock_metrics_df)
        assert flags['zero_variance'] == False
        assert flags['method_switched'] == False
        assert flags['selected_method'] == 'pearson'
        assert flags['vif_value'] < 5.0

    def test_zero_variance_flags_spearman(self, mock_zero_var_df):
        """Test that zero variance in control variable flags and switches method."""
        flags = check_vif_and_select_method(mock_zero_var_df)
        assert flags['zero_variance'] == True
        assert flags['method_switched'] == True
        assert flags['selected_method'] == 'spearman'
        # VIF should be reported as high or infinity (capped in JSON)
        assert flags['vif_value'] > 5.0

    def test_high_collinearity_switches_to_spearman(self, mock_high_collinear_df):
        """Test that high VIF (>5) switches to Spearman."""
        flags = check_vif_and_select_method(mock_high_collinear_df)
        assert flags['zero_variance'] == False
        assert flags['method_switched'] == True
        assert flags['selected_method'] == 'spearman'
        assert flags['vif_value'] > 5.0

    def test_output_file_created(self, mock_metrics_df, tmp_path):
        """Test that quality_flags.json is written to disk."""
        # Mock the output path by temporarily changing the working directory or
        # by patching the function. For simplicity, we assume the function writes to data/processed.
        # We will run it and check if the file exists in the expected location.
        # Since we can't easily mock Path("data/processed") without affecting global state,
        # we will just verify the function runs without error and returns the dict.
        # The file creation is side-effect tested in integration tests.
        
        # Ensure data/processed exists
        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a dummy subject_metrics.csv for load_subject_metrics_data to work if needed
        # But check_vif_and_select_method takes df directly.
        flags = check_vif_and_select_method(mock_metrics_df)
        
        output_file = Path("data/processed/quality_flags.json")
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            saved_flags = json.load(f)
        
        assert 'selected_method' in saved_flags
        assert saved_flags['selected_method'] == 'pearson'