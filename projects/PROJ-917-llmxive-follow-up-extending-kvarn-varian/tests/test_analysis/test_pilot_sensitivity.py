import pytest
import numpy as np
from pathlib import Path
import json
import sys
import os
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.run_pilot_sensitivity import run_pilot_analysis

class TestPilotSensitivityAnalysis:
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.temp_dir, "test_pilot.json")
        
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_pilot_execution_creates_file(self):
        """Test that the pilot analysis creates the output file."""
        run_pilot_analysis(self.output_path, num_matrices=10)
        assert os.path.exists(self.output_path), "Output file was not created"
    
    def test_pilot_output_structure(self):
        """Test that the output JSON has the expected structure."""
        run_pilot_analysis(self.output_path, num_matrices=10)
        
        with open(self.output_path, 'r') as f:
            data = json.load(f)
        
        assert "num_matrices" in data
        assert "epsilon_values" in data
        assert "results_by_epsilon" in data
        assert "validation_status" in data
        assert data["num_matrices"] == 10
    
    def test_pilot_results_have_metrics(self):
        """Test that results for each epsilon contain required metrics."""
        run_pilot_analysis(self.output_path, num_matrices=10)
        
        with open(self.output_path, 'r') as f:
            data = json.load(f)
        
        for eps_str, result in data["results_by_epsilon"].items():
            if "error" not in result:
                assert "avg_kl_delta_per_step" in result
                assert "std_kl_delta_per_step" in result
                assert "num_convergence_failures" in result
                assert "is_monotonic_or_within_bounds" in result
                assert isinstance(result["avg_kl_delta_per_step"], float)
                assert result["num_convergence_failures"] >= 0
    
    def test_validation_status_is_valid(self):
        """Test that validation status is one of the expected values."""
        run_pilot_analysis(self.output_path, num_matrices=10)
        
        with open(self.output_path, 'r') as f:
            data = json.load(f)
        
        valid_statuses = ["passed", "flag_for_review", "unknown"]
        assert data["validation_status"] in valid_statuses
    
    def test_monotonicity_check_logic(self):
        """Test that the monotonicity check runs without error."""
        # This is implicitly tested by the execution, but we can verify
        # that the flag is set for at least one epsilon
        run_pilot_analysis(self.output_path, num_matrices=20)
        
        with open(self.output_path, 'r') as f:
            data = json.load(f)
        
        for eps_str, result in data["results_by_epsilon"].items():
            if "error" not in result:
                assert "is_monotonic_or_within_bounds" in result
                assert isinstance(result["is_monotonic_or_within_bounds"], bool)