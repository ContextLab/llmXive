import os
import json
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

# Import functions to test
from code.analysis import run_baseline_analysis, load_datasets_from_raw
from code.config import get_config

class TestBaselineAnalysis:
    
    def setup_method(self):
        """Create temporary directory with dummy data."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = os.path.join(self.temp_dir, "raw")
        self.output_dir = os.path.join(self.temp_dir, "processed")
        os.makedirs(self.raw_dir)
        os.makedirs(self.output_dir)
        
        # Create a dummy CSV with valid data for t-test and regression
        data = {
            'predictor': [0, 0, 0, 1, 1, 1, 0, 1, 0, 1],
            'outcome': [10.0, 12.0, 11.0, 20.0, 22.0, 21.0, 10.5, 20.5, 11.5, 21.5]
        }
        df = pd.DataFrame(data)
        self.test_file = os.path.join(self.raw_dir, "test_dataset.csv")
        df.to_csv(self.test_file, index=False)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_run_baseline_analysis_writes_file(self):
        """Test that run_baseline_analysis writes a valid JSON file."""
        output_file = os.path.join(self.output_dir, "baseline_metrics.json")
        config = get_config()
        
        success = run_baseline_analysis(self.raw_dir, output_file, config=config)
        
        assert success is True
        assert os.path.exists(output_file)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "generated_at" in data
        assert "datasets" in data
        assert len(data["datasets"]) > 0

    def test_p_values_in_range(self):
        """Verify p-values are strictly between 0 and 1."""
        output_file = os.path.join(self.output_dir, "baseline_metrics.json")
        config = get_config()
        
        run_baseline_analysis(self.raw_dir, output_file, config=config)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        for dataset in data["datasets"]:
            t_test = dataset.get("t_test", {})
            p_val = t_test.get("p_value")
            
            if p_val is not None:
                assert 0 < p_val < 1, f"p-value {p_val} out of range for {dataset['dataset_name']}"
            
            reg = dataset.get("regression", {})
            p_values = reg.get("p_values", [])
            for p in p_values:
                if p is not None:
                    assert 0 <= p <= 1, f"Regression p-value {p} out of range"

    def test_confidence_intervals_finite(self):
        """Verify CI bounds are finite numbers."""
        output_file = os.path.join(self.output_dir, "baseline_metrics.json")
        config = get_config()
        
        run_baseline_analysis(self.raw_dir, output_file, config=config)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        for dataset in data["datasets"]:
            t_test = dataset.get("t_test", {})
            ci = t_test.get("ci")
            
            if ci is not None and len(ci) == 2:
                assert np.isfinite(ci[0]), f"CI lower bound not finite"
                assert np.isfinite(ci[1]), f"CI upper bound not finite"

    def test_output_structure(self):
        """Verify the structure of the output JSON."""
        output_file = os.path.join(self.output_dir, "baseline_metrics.json")
        config = get_config()
        
        run_baseline_analysis(self.raw_dir, output_file, config=config)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "generated_at" in data
        assert isinstance(data["generated_at"], str)
        
        datasets = data["datasets"]
        assert isinstance(datasets, list)
        
        for ds in datasets:
            assert "dataset_name" in ds
            assert "n_rows" in ds
            assert "t_test" in ds
            assert "regression" in ds
            assert "effect_size" in ds
