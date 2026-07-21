"""
Unit tests for verify_streaming_performance.py (T063a).
"""
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from verify_streaming_performance import (
    simulate_large_dataset_streaming,
    simulate_analysis_phase,
    main
)

class TestStreamingPerformanceVerification(unittest.TestCase):

    def test_simulate_large_dataset_streaming_logic(self):
        """Test that streaming simulation processes data in chunks and accumulates stats."""
        n = 1000
        seed = 42
        result = simulate_large_dataset_streaming(n, seed)
        
        self.assertIn('ingestion_duration_seconds', result)
        self.assertEqual(result['subjects_processed'], n)
        self.assertIn('online_stats', result)
        self.assertGreater(result['ingestion_duration_seconds'], 0)

    def test_simulate_analysis_phase_small_dataset(self):
        """Test analysis phase for small dataset (no GPU trigger)."""
        n = 500
        result = simulate_analysis_phase(n)
        
        self.assertEqual(result['method_selected'], 'ZINB') # Based on simulated zero rate > 0.30
        self.assertFalse(result['needs_gpu'])
        self.assertFalse(result['gpu_triggered'])

    def test_simulate_analysis_phase_large_dataset_gpu_trigger(self):
        """Test analysis phase for large dataset (GPU trigger expected)."""
        n = 2000
        result = simulate_analysis_phase(n)
        
        self.assertEqual(result['method_selected'], 'ZINB')
        self.assertTrue(result['needs_gpu'])
        # GPU trigger depends on availability, but logic should flag it
        if not result['gpu_available']:
            self.assertTrue(result['gpu_triggered'])
            self.assertIsNotNone(result['gpu_error_message'])
        else:
            self.assertFalse(result['gpu_triggered'])

    def test_report_generation(self):
        """Test that the main function generates the correct output file."""
        with patch('verify_streaming_performance.simulate_large_dataset_streaming') as mock_ingest, \
             patch('verify_streaming_performance.simulate_analysis_phase') as mock_analysis:
            
            mock_ingest.return_value = {
                'ingestion_duration_seconds': 10.0,
                'subjects_processed': 2000,
                'online_stats': {}
            }
            mock_analysis.return_value = {
                'method_selected': 'ZINB',
                'needs_gpu': True,
                'gpu_available': False,
                'gpu_triggered': True,
                'gpu_error_message': 'GPU required...',
                'analysis_duration_seconds': 5.0
            }
            
            # Run main with specific args to avoid CLI parsing in test
            # We need to patch sys.argv to simulate command line args
            original_argv = sys.argv
            sys.argv = ['verify_streaming_performance.py', '--n', '2000', '--seed', '42']
            
            try:
                exit_code = main()
                
                # Verify output file exists
                output_path = project_root / 'data' / 'results' / 'streaming_performance_report.json'
                self.assertTrue(output_path.exists())
                
                with open(output_path, 'r') as f:
                    report = json.load(f)
                
                self.assertEqual(report['status'], 'PASS') # Should pass with mocked fast times
                self.assertIn('details', report)
                
            finally:
                sys.argv = original_argv

if __name__ == '__main__':
    unittest.main()