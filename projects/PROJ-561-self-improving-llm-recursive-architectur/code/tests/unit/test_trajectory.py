"""
Unit tests for capacity normalization analysis in trajectory.py.
"""
import unittest
import os
import sys
import tempfile
import json
from unittest.mock import patch, MagicMock
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.trajectory import analyze_capacity_normalization, update_trajectory_with_capacity_analysis
from results.trajectory_schema import write_trajectory, read_trajectory


class TestCapacityNormalizationAnalysis(unittest.TestCase):
    """Test suite for capacity normalization analysis."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_trajectory = {
            'metadata': {
                'created_at': '2024-01-01T00:00:00',
                'version': '1.0'
            },
            'cycles': [
                {
                    'cycle_number': 0,
                    'parameter_count': 124000000,  # 124M
                    'gsm8k_accuracy': 0.15,
                    'arc_challenge_accuracy': 0.35,
                    'boolq_ece': 0.25,
                    'flops': 1e12,
                    'training_time_seconds': 3600
                },
                {
                    'cycle_number': 1,
                    'parameter_count': 130000000,  # 130M
                    'gsm8k_accuracy': 0.18,
                    'arc_challenge_accuracy': 0.38,
                    'boolq_ece': 0.22,
                    'flops': 1.1e12,
                    'training_time_seconds': 3800
                },
                {
                    'cycle_number': 2,
                    'parameter_count': 135000000,  # 135M
                    'gsm8k_accuracy': 0.22,
                    'arc_challenge_accuracy': 0.42,
                    'boolq_ece': 0.20,
                    'flops': 1.2e12,
                    'training_time_seconds': 4000
                }
            ]
        }

    def test_analyze_capacity_normalization_basic(self):
        """Test basic capacity normalization analysis with valid data."""
        result = analyze_capacity_normalization(self.test_trajectory)
        
        # Check that analysis was performed
        self.assertIn('correlation_coefficient', result)
        self.assertIn('p_value', result)
        self.assertIn('normalization_factor', result)
        self.assertIn('analysis_summary', result)
        
        # Check that correlation is calculated (should be positive since params and perf increase together)
        self.assertIsNotNone(result['correlation_coefficient'])
        self.assertIsNotNone(result['p_value'])
        
        # Check that normalization factor is reasonable
        self.assertGreater(result['normalization_factor'], 0)
        
        # Check that cycle data is included
        self.assertIn('cycle_data', result)
        self.assertEqual(len(result['cycle_data']), 3)

    def test_analyze_capacity_normalization_empty_cycles(self):
        """Test analysis with no cycles."""
        empty_trajectory = {'cycles': []}
        result = analyze_capacity_normalization(empty_trajectory)
        
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'No cycles found in trajectory data')
        self.assertIsNone(result['correlation_coefficient'])

    def test_analyze_capacity_normalization_insufficient_data(self):
        """Test analysis with only one cycle."""
        single_cycle_trajectory = {
            'cycles': [
                {
                    'cycle_number': 0,
                    'parameter_count': 124000000,
                    'gsm8k_accuracy': 0.15,
                    'arc_challenge_accuracy': 0.35,
                    'boolq_ece': 0.25
                }
            ]
        }
        result = analyze_capacity_normalization(single_cycle_trajectory)
        
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'Insufficient data points for correlation analysis')

    def test_analyze_capacity_normalization_trend_detection(self):
        """Test that trend is correctly identified."""
        # Create data with positive correlation
        result = analyze_capacity_normalization(self.test_trajectory)
        
        # Since params and performance both increase, trend should indicate capacity-driven
        self.assertIn('trend', result)
        self.assertIsNotNone(result['trend'])

    def test_update_trajectory_with_capacity_analysis(self):
        """Test updating trajectory file with analysis results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            trajectory_path = os.path.join(tmpdir, 'trajectory.json')
            
            # Write initial trajectory
            write_trajectory(self.test_trajectory, trajectory_path)
            
            # Update with analysis
            result = update_trajectory_with_capacity_analysis(trajectory_path)
            
            # Verify analysis was added
            self.assertIn('capacity_normalization_analysis', result)
            self.assertIsNotNone(result['capacity_normalization_analysis'])
            
            # Verify file was updated
            with open(trajectory_path, 'r') as f:
                updated_data = json.load(f)
            
            self.assertIn('capacity_normalization_analysis', updated_data)
            self.assertIsNotNone(updated_data['capacity_normalization_analysis'])

    def test_analysis_summary_content(self):
        """Test that analysis summary contains expected information."""
        result = analyze_capacity_normalization(self.test_trajectory)
        
        summary = result['analysis_summary']
        
        # Check for key phrases
        self.assertIn('Capacity Normalization Analysis', summary)
        self.assertIn('Correlation coefficient', summary)
        self.assertIn('p=', summary)
        self.assertIn('per million parameters', summary)

    def test_cycle_data_structure(self):
        """Test that cycle data has correct structure."""
        result = analyze_capacity_normalization(self.test_trajectory)
        
        cycle_data = result['cycle_data']
        
        for item in cycle_data:
            self.assertIn('cycle', item)
            self.assertIn('params', item)
            self.assertIn('performance', item)
            self.assertIn('gsm8k', item)
            self.assertIn('arc', item)
            self.assertIn('boolq', item)


if __name__ == '__main__':
    unittest.main()