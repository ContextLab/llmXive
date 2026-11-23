import pytest
import json
import os
import tempfile
from pathlib import Path
import numpy as np
import csv

from code.analyze_pvalues import (
    load_embarrassment_log,
    classify_failure_modes,
    calculate_ks_statistic
)

class TestClassifyFailureModes:
    @pytest.fixture
    def temp_log_file(self):
        # Create a temporary CSV file for the embarrassment log
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', dir='data/results') as f:
            writer = csv.writer(f)
            writer.writerow(['seed', 'rho', 'n', 'p', 'distribution_type', 'ks_stat'])
            # Add some test data
            # Scenario 1: High KS, high p/n, high rho
            writer.writerow([1, 0.9, 50, 5000, 'normal', 0.15])
            # Scenario 2: High KS, lower p/n
            writer.writerow([2, 0.9, 100, 5000, 'normal', 0.14])
            # Scenario 3: Lower KS
            writer.writerow([3, 0.5, 50, 5000, 'normal', 0.05])
            # Scenario 4: Same KS as 1, but lower p/n
            writer.writerow([4, 0.9, 100, 1000, 'normal', 0.15])
            
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    def test_load_embarrassment_log(self, temp_log_file):
        logs = load_embarrassment_log(temp_log_file)
        assert len(logs) == 4
        assert logs[0]['seed'] == 1
        assert logs[0]['ks_stat'] == 0.15

    def test_classify_failure_modes_sorting(self, temp_log_file):
        # Mock the path used in the function by temporarily replacing the default
        # Since the function uses hardcoded paths, we need to ensure the file is in the expected location
        # or modify the function to accept a path. For this test, we assume the file is moved/renamed.
        # Actually, the function `classify_failure_modes` uses hardcoded path "data/results/embarrassment_log.csv".
        # We must ensure the temp file is at that location or mock the function.
        # To keep it simple, let's just test the logic by creating the file in the expected spot.
        
        expected_path = "data/results/embarrassment_log.csv"
        os.makedirs("data/results", exist_ok=True)
        # Copy temp content to expected path
        with open(temp_log_file, 'r') as src, open(expected_path, 'w') as dst:
            dst.write(src.read())
        
        try:
            result = classify_failure_modes()
            assert result['found'] is True
            worst = result['worst_case_scenario']
            
            # Expected winner: seed 1 (KS=0.15, p/n=100, rho=0.9)
            # Seed 4 has KS=0.15, but p/n=10 (1000/100). Seed 1 has p/n=100.
            # So seed 1 should win.
            assert worst['seed'] == 1
            assert worst['ks_stat'] == 0.15
            assert worst['p_over_n'] == 100.0
        finally:
            os.unlink(expected_path)

    def test_classify_failure_modes_empty_log(self):
        expected_path = "data/results/embarrassment_log.csv"
        os.makedirs("data/results", exist_ok=True)
        # Create empty file with header
        with open(expected_path, 'w') as f:
            f.write("seed,rho,n,p,distribution_type,ks_stat\n")
        
        try:
            result = classify_failure_modes()
            assert result['found'] is False
            assert "No entries" in result['reason']
        finally:
            os.unlink(expected_path)

class TestCalculateKsStatistic:
    def test_ks_statistic_calculation(self):
        # Uniform vs Uniform should be low
        u1 = np.random.uniform(0, 1, 1000)
        u2 = np.random.uniform(0, 1, 1000)
        ks = calculate_ks_statistic(u1, u2)
        assert ks < 0.1 # Should be close

    def test_ks_statistic_different_distributions(self):
        # Uniform vs Normal (mapped to 0-1 via CDF? No, just raw values)
        # If we compare U[0,1] and N(0,1), the CDFs will be very different.
        u = np.random.uniform(0, 1, 1000)
        n = np.random.normal(0, 1, 1000)
        ks = calculate_ks_statistic(u, n)
        assert ks > 0.1 # Should be significant