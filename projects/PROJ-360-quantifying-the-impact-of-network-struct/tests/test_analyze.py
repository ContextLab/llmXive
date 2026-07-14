import pytest
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import logging

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from analyze import (
    log_power_analysis_warning,
    setup_analysis_logger,
    apply_bonferroni_correction,
    calculate_vif,
    get_network_metrics
)

class TestPowerAnalysisLogging:
    """Tests for T018: Power analysis logging."""

    def setup_method(self):
        self.log_path = Path(__file__).resolve().parent.parent / "results" / "power_analysis.log"
        # Ensure results directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        # Clear log file if it exists
        if self.log_path.exists():
            self.log_path.unlink()

    def test_log_warning_when_n_less_than_50(self, tmp_path):
        """Verify warning is logged when n < 50."""
        # Use a temporary file for this test to avoid side effects
        test_log_path = tmp_path / "test_power.log"
        
        logger = setup_analysis_logger("test_power")
        # Remove existing handlers to avoid duplication in tests
        logger.handlers = []
        handler = logging.FileHandler(test_log_path)
        logger.addHandler(handler)
        
        n = 20
        log_power_analysis_warning(n, logger)
        
        handler.close() # Flush
          
        assert test_log_path.exists()
        content = test_log_path.read_text()
        assert "WARNING" in content
        assert "20" in content
        assert "50" in content

    def test_log_info_when_n_greater_than_50(self, tmp_path):
        """Verify info is logged when n >= 50."""
        test_log_path = tmp_path / "test_power_ok.log"
        
        logger = setup_analysis_logger("test_power_ok")
        logger.handlers = []
        handler = logging.FileHandler(test_log_path)
        logger.addHandler(handler)
        
        n = 100
        log_power_analysis_warning(n, logger)
        
        handler.close()
        
        assert test_log_path.exists()
        content = test_log_path.read_text()
        assert "WARNING" not in content
        assert "100" in content
        assert "50" in content
        assert "meets the threshold" in content.lower()

class TestBonferroniCorrection:
    """Tests for T017: Bonferroni correction."""

    def test_bonferroni_multiplies_p_value(self):
        """Verify p-values are multiplied by number of tests."""
        n_tests = 3
        alpha = 0.05
        
        # Mock correlation results
        mock_results = {
            "pearson": {
                "average_degree": {"r": 0.5, "p": 0.01},
                "average_shortest_path_length": {"r": -0.2, "p": 0.04},
                "clustering_coefficient": {"r": 0.1, "p": 0.03}
            },
            "spearman": {
                "average_degree": {"r": 0.5, "p": 0.01},
                "average_shortest_path_length": {"r": -0.2, "p": 0.04},
                "clustering_coefficient": {"r": 0.1, "p": 0.03}
            },
            "sample_size": 60
        }
        
        corrected = apply_bonferroni_correction(mock_results)
        
        # Check correction logic (p * 3)
        assert abs(corrected["pearson"]["average_degree"]["p_bonferroni"] - 0.03) < 1e-9
        assert abs(corrected["pearson"]["average_shortest_path_length"]["p_bonferroni"] - 0.12) < 1e-9
        assert abs(corrected["pearson"]["clustering_coefficient"]["p_bonferroni"] - 0.09) < 1e-9
        
        # Check that p > 1.0 is capped
        mock_high_p = {
            "pearson": {"m1": {"r": 0, "p": 0.5}},
            "spearman": {"m1": {"r": 0, "p": 0.5}},
            "sample_size": 10
        }
        corrected_high = apply_bonferroni_correction(mock_high_p)
        assert corrected_high["pearson"]["m1"]["p_bonferroni"] == 1.0

class TestVIFCalculation:
    """Tests for T020: VIF Calculation."""

    def test_vif_calculation_basic(self):
        """Test VIF calculation with simple data."""
        # Create a DataFrame with some correlation
        data = {
            'average_degree': [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0],
            'average_shortest_path_length': [1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0],
            'clustering_coefficient': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            'thermal_conductivity_scalar': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        }
        df = pd.DataFrame(data)
        
        vif_results = calculate_vif(df)
        
        assert 'average_degree' in vif_results
        assert 'average_shortest_path_length' in vif_results
        assert 'clustering_coefficient' in vif_results
        
        # VIF should be >= 1.0
        for val in vif_results.values():
            assert val >= 1.0

    def test_vif_high_collinearity(self):
        """Test VIF with high collinearity."""
        # Create data with perfect collinearity (VIF should be very high or inf)
        data = {
            'average_degree': [1.0, 2.0, 3.0, 4.0, 5.0],
            'average_shortest_path_length': [1.0, 2.0, 3.0, 4.0, 5.0], # Identical
            'clustering_coefficient': [1.0, 2.0, 3.0, 4.0, 5.0],
            'thermal_conductivity_scalar': [10, 20, 30, 40, 50]
        }
        df = pd.DataFrame(data)
        
        vif_results = calculate_vif(df)
        
        # At least one VIF should be very high
        assert max(vif_results.values()) > 100.0 # Or inf

class TestNetworkMetrics:
    """Tests for helper functions."""

    def test_get_network_metrics(self):
        """Verify correct metric names are returned."""
        metrics = get_network_metrics(pd.DataFrame())
        expected = ['average_degree', 'average_shortest_path_length', 'clustering_coefficient']
        assert metrics == expected