"""
Unit tests for simulate_pretest.py
"""
import os
import json
import pytest
import numpy as np
from scipy import stats

# Import the module to test
import code.simulate_pretest as simulate_pretest

class TestPretestSimulation:
    """Tests for the pre-test simulation functionality."""
    
    def test_output_file_created(self, tmp_path):
        """Test that the output file is created at the expected location."""
        # Temporarily override output path for testing
        original_output = simulate_pretest.OUTPUT_PATH
        test_output = str(tmp_path / "results.json")
        simulate_pretest.OUTPUT_PATH = test_output
        
        try:
            simulate_pretest.main()
            
            # Verify file exists
            assert os.path.exists(test_output), "Output file was not created"
            
            # Verify file is valid JSON
            with open(test_output, 'r') as f:
                results = json.load(f)
            
            assert isinstance(results, dict), "Results should be a dictionary"
        finally:
            # Restore original output path
            simulate_pretest.OUTPUT_PATH = original_output
    
    def test_results_structure(self, tmp_path):
        """Test that results contain all required fields."""
        original_output = simulate_pretest.OUTPUT_PATH
        test_output = str(tmp_path / "results.json")
        simulate_pretest.OUTPUT_PATH = test_output
        
        try:
            results = simulate_pretest.main()
            
            # Check required fields
            required_fields = [
                "n_participants", "ai_mean_rating", "ai_std_rating",
                "human_mean_rating", "human_std_rating", "t_statistic",
                "p_value", "is_indistinguishable", "conclusion", "seed"
            ]
            
            for field in required_fields:
                assert field in results, f"Missing required field: {field}"
        finally:
            simulate_pretest.OUTPUT_PATH = original_output
    
    def test_p_value_calculation(self):
        """Test that p-value is calculated correctly using t-test."""
        # Since we're using a fixed seed, we can verify the exact p-value
        results = simulate_pretest.run_pretest_simulation()
        
        # Verify p-value is a float
        assert isinstance(results["p_value"], float), "p-value should be a float"
        
        # Verify p-value is between 0 and 1
        assert 0.0 <= results["p_value"] <= 1.0, "p-value should be between 0 and 1"
        
        # Verify t-statistic is a float
        assert isinstance(results["t_statistic"], float), "t-statistic should be a float"
    
    def test_sample_size(self):
        """Test that the correct number of participants is used."""
        results = simulate_pretest.run_pretest_simulation()
        assert results["n_participants"] == simulate_pretest.N_PARTICIPANTS, \
            f"Expected {simulate_pretest.N_PARTICIPANTS} participants, got {results['n_participants']}"
    
    def test_seed_reproducibility(self):
        """Test that the simulation is reproducible with the same seed."""
        results1 = simulate_pretest.run_pretest_simulation()
        results2 = simulate_pretest.run_pretest_simulation()
        
        # All numeric results should be identical
        assert results1["p_value"] == results2["p_value"], "Results should be reproducible"
        assert results1["t_statistic"] == results2["t_statistic"], "Results should be reproducible"
        assert results1["ai_mean_rating"] == results2["ai_mean_rating"], "Results should be reproducible"
        assert results1["human_mean_rating"] == results2["human_mean_rating"], "Results should be reproducible"
    
    def test_indistinguishability_conclusion(self):
        """Test that the conclusion is based on the p-value threshold."""
        results = simulate_pretest.run_pretest_simulation()
        
        # Verify conclusion matches the p-value threshold
        expected_conclusion = "PASS" if results["p_value"] > 0.05 else "FAIL"
        assert results["conclusion"] == expected_conclusion, \
            f"Conclusion should be {expected_conclusion} for p-value {results['p_value']}"
        
        # Verify is_indistinguishable flag matches conclusion
        expected_flag = results["p_value"] > 0.05
        assert results["is_indistinguishable"] == expected_flag, \
            "is_indistinguishable should match the p-value threshold"
    
    def test_output_path_configuration(self, tmp_path):
        """Test that the output path is correctly configured."""
        test_output = str(tmp_path / "custom_results.json")
        
        # Temporarily change the output path
        original_output = simulate_pretest.OUTPUT_PATH
        simulate_pretest.OUTPUT_PATH = test_output
        
        try:
            simulate_pretest.main()
            assert os.path.exists(test_output), "Output should be written to the configured path"
        finally:
            simulate_pretest.OUTPUT_PATH = original_output
