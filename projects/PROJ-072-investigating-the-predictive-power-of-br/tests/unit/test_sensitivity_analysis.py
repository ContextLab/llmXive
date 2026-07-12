import os
import sys
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from classification.sensitivity_analysis import (
    load_analysis_config,
    load_features,
    generate_simulated_med_status,
    run_sensitivity_analysis
)

class TestSensitivityAnalysis:

    def test_generate_simulated_med_status_shape(self):
        """Test that the generated array has the correct shape."""
        n = 50
        result = generate_simulated_med_status(n, seed=42)
        assert result.shape == (n,), f"Expected shape ({n},), got {result.shape}"

    def test_generate_simulated_med_status_values(self):
        """Test that generated values are binary (0 or 1)."""
        n = 100
        result = generate_simulated_med_status(n, seed=42)
        unique_vals = np.unique(result)
        # Should only contain 0 and 1
        assert set(unique_vals).issubset({0, 1}), f"Unexpected values: {unique_vals}"

    def test_generate_simulated_med_status_deterministic(self):
        """Test that the same seed produces the same result."""
        n = 20
        result1 = generate_simulated_med_status(n, seed=42)
        result2 = generate_simulated_med_status(n, seed=42)
        assert np.array_equal(result1, result2), "Results with same seed should be identical"

    def test_run_sensitivity_analysis_skip_if_available(self, tmp_path):
        """Test that simulation is skipped if medication data is available."""
        # Setup config
        config_data = {'medication_status_available': True}
        config_file = tmp_path / 'analysis_config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Setup features
        features_file = tmp_path / 'features.csv'
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
        df.to_csv(features_file, index=False)
        
        output_file = tmp_path / 'features_sim_med.csv'
        
        # Run
        result = run_sensitivity_analysis(config_file, features_file, output_file)
        
        # Assert
        assert result is True
        assert not output_file.exists(), "Output file should not be created if simulation is skipped"

    def test_run_sensitivity_analysis_generate_if_missing(self, tmp_path):
        """Test that simulation is generated if medication data is missing."""
        # Setup config (missing key implies False)
        config_data = {'medication_status_available': False}
        config_file = tmp_path / 'analysis_config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Setup features
        features_file = tmp_path / 'features.csv'
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
        df.to_csv(features_file, index=False)
        
        output_file = tmp_path / 'features_sim_med.csv'
        
        # Run
        result = run_sensitivity_analysis(config_file, features_file, output_file)
        
        # Assert
        assert result is True
        assert output_file.exists(), "Output file should be created"
        
        # Verify content
        df_out = pd.read_csv(output_file)
        assert 'sim_med_status' in df_out.columns
        assert len(df_out) == 3
        # Verify values are binary
        assert set(df_out['sim_med_status'].unique()).issubset({0, 1})

    def test_run_sensitivity_analysis_file_not_found_features(self, tmp_path):
        """Test error handling when features file is missing."""
        config_file = tmp_path / 'analysis_config.json'
        with open(config_file, 'w') as f:
            json.dump({'medication_status_available': False}, f)
        
        features_file = tmp_path / 'nonexistent.csv'
        output_file = tmp_path / 'out.csv'
        
        result = run_sensitivity_analysis(config_file, features_file, output_file)
        assert result is False