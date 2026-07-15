import pytest
import os
import json
import numpy as np
from unittest.mock import patch, MagicMock

from code.analysis.validation_metrics import (
    calculate_ks_distance,
    calculate_real_data_power,
    calculate_validation_metrics,
    save_validation_metrics,
    load_simulated_pvalues_for_comparison
)

class TestValidationMetrics:
    
    def test_calculate_ks_distance_empty_lists(self):
        """Test KS distance with empty lists returns NaN"""
        result = calculate_ks_distance([], [])
        assert np.isnan(result)
    
    def test_calculate_ks_distance_identical_distributions(self):
        """Test KS distance with identical distributions is near zero"""
        np.random.seed(42)
        dist = np.random.uniform(0, 1, 1000)
        result = calculate_ks_distance(dist.tolist(), dist.tolist())
        assert result < 0.05
    
    def test_calculate_ks_distance_different_distributions(self):
        """Test KS distance with very different distributions is larger"""
        dist1 = np.random.uniform(0, 1, 1000)
        dist2 = np.random.beta(2, 5, 1000)  # Skewed distribution
        result = calculate_ks_distance(dist1.tolist(), dist2.tolist())
        assert result > 0.05
    
    def test_calculate_real_data_power_all_significant(self):
        """Test power calculation when all p-values are significant"""
        p_values = [0.01, 0.02, 0.03, 0.04]
        power = calculate_real_data_power(p_values, alpha=0.05)
        assert power == 1.0
    
    def test_calculate_real_data_power_none_significant(self):
        """Test power calculation when no p-values are significant"""
        p_values = [0.1, 0.2, 0.3, 0.4]
        power = calculate_real_data_power(p_values, alpha=0.05)
        assert power == 0.0
    
    def test_calculate_real_data_power_half_significant(self):
        """Test power calculation when half p-values are significant"""
        p_values = [0.01, 0.02, 0.1, 0.2]
        power = calculate_real_data_power(p_values, alpha=0.05)
        assert power == 0.5
    
    def test_calculate_real_data_power_empty_list(self):
        """Test power calculation with empty list returns 0"""
        power = calculate_real_data_power([], alpha=0.05)
        assert power == 0.0
    
    def test_save_validation_metrics_creates_file(self):
        """Test that save_validation_metrics creates the output file"""
        metrics = {
            "test_type": "t-test",
            "effect_size": 0.5,
            "sample_size": 30,
            "validation_passed": True
        }
        
        output_path = "data/simulation/test_validation_metrics_temp.json"
        try:
            save_validation_metrics(metrics, output_path)
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
                assert len(loaded) == 1
                assert loaded[0]["test_type"] == "t-test"
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_save_validation_metrics_appends_to_existing(self):
        """Test that save_validation_metrics appends to existing file"""
        metrics1 = {"test_type": "t-test", "id": 1}
        metrics2 = {"test_type": "anova", "id": 2}
        
        output_path = "data/simulation/test_validation_metrics_append.json"
        try:
            save_validation_metrics(metrics1, output_path)
            save_validation_metrics(metrics2, output_path)
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
                assert len(loaded) == 2
                assert loaded[0]["id"] == 1
                assert loaded[1]["id"] == 2
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    @patch('code.analysis.validation_metrics.load_real_data_pvalues')
    @patch('code.analysis.validation_metrics.load_simulated_pvalues_for_comparison')
    def test_calculate_validation_metrics_success(self, mock_sim, mock_real):
        """Test successful calculation of validation metrics"""
        mock_real.return_value = [0.01, 0.02, 0.03]
        mock_sim.return_value = [0.02, 0.03, 0.04]
        
        metrics = calculate_validation_metrics("t-test", 0.5, 30)
        
        assert metrics["test_type"] == "t-test"
        assert metrics["effect_size"] == 0.5
        assert metrics["sample_size"] == 30
        assert metrics["real_data_power"] == 1.0  # All significant
        assert metrics["validation_passed"] is True
        assert "ks_distance" in metrics
    
    @patch('code.analysis.validation_metrics.load_real_data_pvalues')
    def test_calculate_validation_metrics_no_real_data(self, mock_real):
        """Test validation metrics when no real data available"""
        mock_real.return_value = []
        
        metrics = calculate_validation_metrics("t-test", 0.5, 30)
        
        assert metrics["validation_passed"] is False
        assert "No real data p-values available" in metrics["reasons"]
    
    @patch('code.analysis.validation_metrics.load_real_data_pvalues')
    @patch('code.analysis.validation_metrics.load_simulated_pvalues_for_comparison')
    def test_calculate_validation_metrics_ks_exceeds_threshold(self, mock_sim, mock_real):
        """Test validation fails when KS distance exceeds threshold"""
        # Create distributions that will have high KS distance
        mock_real.return_value = np.random.beta(2, 5, 100).tolist()
        mock_sim.return_value = np.random.beta(5, 2, 100).tolist()
        
        metrics = calculate_validation_metrics("t-test", 0.5, 30, ks_threshold=0.01)
        
        assert metrics["validation_passed"] is False
        assert any("KS distance" in reason for reason in metrics["reasons"])
        assert any("exceeds threshold" in reason for reason in metrics["reasons"])