import pytest
import math
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple
from unittest.mock import patch, MagicMock

# Import from the project's robustness module (which T025 will implement)
# We import what we expect to exist based on the API surface plan.
# If T025 hasn't run yet, we mock the functions or test the logic in isolation.
try:
    from src.robustness import (
        run_sensitivity_sweep,
        load_convergence_data_for_sweep,
        compute_correlation_for_threshold,
        analyze_threshold_stability,
        generate_sensitivity_report
    )
    ROBUSTNESS_MODULE_AVAILABLE = True
except ImportError:
    ROBUSTNESS_MODULE_AVAILABLE = False
    # Define stubs for testing if the module isn't ready yet
    def run_sensitivity_sweep(*args, **kwargs):
        pass
    def load_convergence_data_for_sweep(*args, **kwargs):
        pass
    def compute_correlation_for_threshold(*args, **kwargs):
        pass
    def analyze_threshold_stability(*args, **kwargs):
        pass
    def generate_sensitivity_report(*args, **kwargs):
        pass

# Fixtures and Mock Data
@pytest.fixture
def temp_dir():
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

@pytest.fixture
def sample_convergence_data():
    """
    Mock data simulating data/processed/convergence_results.csv
    Structure: task_id, k_value, converged_at_k, ...
    """
    return [
        {"task_id": "h1", "k_value": 1, "converged_at_k": 1, "entropy": 0.1},
        {"task_id": "h1", "k_value": 2, "converged_at_k": 1, "entropy": 0.1},
        {"task_id": "h1", "k_value": 3, "converged_at_k": 1, "entropy": 0.1},
        {"task_id": "h1", "k_value": 4, "converged_at_k": 1, "entropy": 0.1},
        {"task_id": "h2", "k_value": 1, "converged_at_k": 2, "entropy": 0.5},
        {"task_id": "h2", "k_value": 2, "converged_at_k": 2, "entropy": 0.5},
        {"task_id": "h2", "k_value": 3, "converged_at_k": 2, "entropy": 0.5},
        {"task_id": "h2", "k_value": 4, "converged_at_k": 2, "entropy": 0.5},
        {"task_id": "h3", "k_value": 1, "converged_at_k": 3, "entropy": 0.8},
        {"task_id": "h3", "k_value": 2, "converged_at_k": 3, "entropy": 0.8},
        {"task_id": "h3", "k_value": 3, "converged_at_k": 3, "entropy": 0.8},
        {"task_id": "h3", "k_value": 4, "converged_at_k": 3, "entropy": 0.8},
        {"task_id": "h4", "k_value": 1, "converged_at_k": 4, "entropy": 0.9},
        {"task_id": "h4", "k_value": 2, "converged_at_k": 4, "entropy": 0.9},
        {"task_id": "h4", "k_value": 3, "converged_at_k": 4, "entropy": 0.9},
        {"task_id": "h4", "k_value": 4, "converged_at_k": 4, "entropy": 0.9},
    ]

@pytest.fixture
def sample_entropy_data():
    """
    Mock data simulating data/processed/entropy_results.csv
    Structure: task_id, entropy, ...
    """
    return [
        {"task_id": "h1", "entropy": 0.1},
        {"task_id": "h2", "entropy": 0.5},
        {"task_id": "h3", "entropy": 0.8},
        {"task_id": "h4", "entropy": 0.9},
    ]

class TestSensitivitySweepValidation:
    """
    Tests for T024: Sensitivity analysis sweep validation.
    Verifies that the system can re-run inference logic for k=4 (using T013b data)
    and sweep convergence thresholds k in {2, 3, 4} to compute variation in Spearman rho.
    """

    @pytest.mark.skipif(not ROBUSTNESS_MODULE_AVAILABLE, reason="robustness module not yet implemented")
    def test_load_convergence_data_for_sweep(self, temp_dir, sample_convergence_data):
        """Test that the loader correctly aggregates k=1..4 data for sweep."""
        # Write mock data to disk
        data_path = Path(temp_dir) / "convergence_results.csv"
        import csv
        with open(data_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sample_convergence_data[0].keys())
            writer.writeheader()
            writer.writerows(sample_convergence_data)

        # Load
        data = load_convergence_data_for_sweep(str(data_path))
        
        assert len(data) == 4, "Should aggregate to unique task_ids"
        assert "h1" in data
        assert data["h1"]["converged_at_k"] == 1
        assert data["h1"]["entropy"] == 0.1
        assert data["h4"]["converged_at_k"] == 4

    @pytest.mark.skipif(not ROBUSTNESS_MODULE_AVAILABLE, reason="robustness module not yet implemented")
    def test_compute_correlation_for_threshold(self, sample_convergence_data, sample_entropy_data):
        """Test correlation computation for a specific threshold k."""
        # Create a mock dataset for the function
        # The function should filter convergence data where converged_at_k <= threshold
        # and correlate with entropy.
        
        # For k=2: h1 (1<=2), h2 (2<=2), h3 (3>2), h4 (4>2)
        # Converged list: [1, 2, 3, 4] (if we map converged_at_k to a binary 1/0 based on threshold)
        # Actually, the metric is usually: does it converge by k?
        # Let's assume the function handles the mapping internally.
        
        # We test that the function returns a valid float for rho and p-value
        rho, p_val = compute_correlation_for_threshold(
            sample_convergence_data, 
            sample_entropy_data, 
            threshold_k=2
        )
        
        assert isinstance(rho, float), "Correlation must be a float"
        assert isinstance(p_val, float), "P-value must be a float"
        assert -1.0 <= rho <= 1.0, "Correlation must be between -1 and 1"

    @pytest.mark.skipif(not ROBUSTNESS_MODULE_AVAILABLE, reason="robustness module not yet implemented")
    def test_sweep_across_thresholds(self, temp_dir, sample_convergence_data, sample_entropy_data):
        """Test the full sweep across k in {2, 3, 4}."""
        # Write data to disk
        conv_path = Path(temp_dir) / "convergence_results.csv"
        ent_path = Path(temp_dir) / "entropy_results.csv"
        
        import csv
        with open(conv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sample_convergence_data[0].keys())
            writer.writeheader()
            writer.writerows(sample_convergence_data)
        
        with open(ent_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sample_entropy_data[0].keys())
            writer.writeheader()
            writer.writerows(sample_entropy_data)

        # Run sweep
        results = run_sensitivity_sweep(
            conv_path=str(conv_path),
            ent_path=str(ent_path),
            thresholds=[2, 3, 4]
        )
        
        assert len(results) == 3, "Should have results for 3 thresholds"
        for r in results:
            assert "threshold" in r
            assert "rho" in r
            assert "p_value" in r
            assert "stability_metric" in r

    @pytest.mark.skipif(not ROBUSTNESS_MODULE_AVAILABLE, reason="robustness module not yet implemented")
    def test_generate_sensitivity_report(self, temp_dir, sample_convergence_data, sample_entropy_data):
        """Test that the report generation writes a valid JSON file."""
        conv_path = Path(temp_dir) / "convergence_results.csv"
        ent_path = Path(temp_dir) / "entropy_results.csv"
        report_path = Path(temp_dir) / "sensitivity_report.json"
        
        import csv
        with open(conv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sample_convergence_data[0].keys())
            writer.writeheader()
            writer.writerows(sample_convergence_data)
        
        with open(ent_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sample_entropy_data[0].keys())
            writer.writeheader()
            writer.writerows(sample_entropy_data)

        generate_sensitivity_report(
            conv_path=str(conv_path),
            ent_path=str(ent_path),
            output_path=str(report_path),
            thresholds=[2, 3, 4]
        )
        
        assert report_path.exists(), "Report file must be created"
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert "sweep_results" in report
        assert "summary" in report
        assert "variance_in_rho" in report["summary"]

class TestEdgeCases:
    """Tests for edge cases in sensitivity analysis."""

    @pytest.mark.skipif(not ROBUSTNESS_MODULE_AVAILABLE, reason="robustness module not yet implemented")
    def test_no_convergence_at_threshold(self, temp_dir):
        """Test handling when no samples converge at a specific threshold."""
        # Create data where nothing converges by k=2
        data = [
            {"task_id": "h1", "k_value": 1, "converged_at_k": 3, "entropy": 0.1},
            {"task_id": "h1", "k_value": 2, "converged_at_k": 3, "entropy": 0.1},
            {"task_id": "h1", "k_value": 3, "converged_at_k": 3, "entropy": 0.1},
            {"task_id": "h1", "k_value": 4, "converged_at_k": 3, "entropy": 0.1},
        ]
        conv_path = Path(temp_dir) / "conv.csv"
        ent_path = Path(temp_dir) / "ent.csv"
        
        import csv
        with open(conv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        with open(ent_path, 'w', newline='') as f:
            f.write("task_id,entropy\nh1,0.1\n")

        # Should not crash, but return NaN or specific handling
        rho, p = compute_correlation_for_threshold(str(conv_path), str(ent_path), threshold_k=2)
        # Depending on implementation, this might be NaN or 0. We ensure it doesn't crash.
        assert isinstance(rho, (float, type(None)))

    @pytest.mark.skipif(not ROBUSTNESS_MODULE_AVAILABLE, reason="robustness module not yet implemented")
    def test_single_sample(self, temp_dir):
        """Test with only one sample."""
        data = [
            {"task_id": "h1", "k_value": 1, "converged_at_k": 1, "entropy": 0.1},
            {"task_id": "h1", "k_value": 2, "converged_at_k": 1, "entropy": 0.1},
            {"task_id": "h1", "k_value": 3, "converged_at_k": 1, "entropy": 0.1},
            {"task_id": "h1", "k_value": 4, "converged_at_k": 1, "entropy": 0.1},
        ]
        conv_path = Path(temp_dir) / "conv.csv"
        ent_path = Path(temp_dir) / "ent.csv"
        
        import csv
        with open(conv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        with open(ent_path, 'w', newline='') as f:
            f.write("task_id,entropy\nh1,0.1\n")

        # Spearman with 1 sample is undefined (NaN). Ensure graceful handling.
        rho, p = compute_correlation_for_threshold(str(conv_path), str(ent_path), threshold_k=2)
        # Implementation should handle this (e.g., return NaN or raise a specific warning)
        assert isinstance(rho, (float, type(None)))

# If the module is not available, we still define the test structure
# so that when T025 implements robustness.py, these tests will run.
if not ROBUSTNESS_MODULE_AVAILABLE:
    # Re-define the test methods to assert that the module is missing,
    # or simply pass to allow the test suite to run without erroring on import.
    # In a real CI, we would expect T025 to run before T024 tests.
    # For now, we mark them as skipped or pass.
    pass