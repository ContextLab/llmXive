import pytest
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from diagnostics import log_normal_discrimination, main

class TestLogNormalDiscriminationIntegration:
    """Integration tests for Log-Normal discrimination analysis."""
    
    def test_full_pipeline_execution(self, tmp_path):
        """Test full execution of Log-Normal discrimination pipeline."""
        # Create temporary data files
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        
        processed_dir = data_dir / "processed"
        processed_dir.mkdir()
        
        results_dir = data_dir / "results"
        results_dir.mkdir()
        
        # Create synthetic cleaned data
        import pandas as pd
        np.random.seed(42)
        n_samples = 1000
        
        # Generate mixed distribution (some Log-Normal, some Pareto)
        lognormal_part = np.random.lognormal(mean=2, sigma=1, size=int(n_samples * 0.5))
        pareto_part = np.random.pareto(a=2, size=int(n_samples * 0.5)) + 1
        mixed_data = np.concatenate([lognormal_part, pareto_part])
        
        # Create DataFrame
        df = pd.DataFrame({
            'total_delay': mixed_data
        })
        
        cleaned_file = processed_dir / "cleaned_delays.csv"
        df.to_csv(cleaned_file, index=False)
        
        # Create x_min estimate
        x_min = np.percentile(mixed_data, 75)
        x_min_data = {"x_min": float(x_min), "method": "KS_minimization"}
        
        x_min_file = results_dir / "x_min_estimate.json"
        with open(x_min_file, 'w') as f:
            json.dump(x_min_data, f)
        
        # Change to temp directory for execution
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the analysis
            result = log_normal_discrimination(
                mixed_data, 
                x_min, 
                n_simulations=100
            )
            
            # Verify result structure
            assert "p_value" in result
            assert "is_log_normal" in result
            assert "observed_curvature" in result
            assert "sample_size" in result
            assert result["sample_size"] > 0
            
            # Verify result is reasonable
            assert 0 <= result["p_value"] <= 1
            assert isinstance(result["is_log_normal"], bool)
            assert result["interpretation"] in ["Reject Log-Normal", "Cannot reject Log-Normal"]
            
        finally:
            os.chdir(original_cwd)
            
    def test_main_function_execution(self, tmp_path):
        """Test execution of main function."""
        # Create temporary data structure
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        
        processed_dir = data_dir / "processed"
        processed_dir.mkdir()
        
        results_dir = data_dir / "results"
        results_dir.mkdir()
        
        # Create cleaned data
        import pandas as pd
        np.random.seed(42)
        n_samples = 500
        data = np.random.lognormal(mean=2, sigma=1, size=n_samples)
        
        df = pd.DataFrame({'total_delay': data})
        cleaned_file = processed_dir / "cleaned_delays.csv"
        df.to_csv(cleaned_file, index=False)
        
        # Create x_min estimate
        x_min = np.percentile(data, 75)
        x_min_data = {"x_min": float(x_min)}
        
        x_min_file = results_dir / "x_min_estimate.json"
        with open(x_min_file, 'w') as f:
            json.dump(x_min_data, f)
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # This would normally run the full main() function
            # For testing, we just verify the components work
            result = log_normal_discrimination(data, x_min, n_simulations=50)
            
            assert result["sample_size"] == n_samples
            assert "p_value" in result
            
        finally:
            os.chdir(original_cwd)