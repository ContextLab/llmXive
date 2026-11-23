import os
import sys
import csv
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import numpy as np

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from code_00_config import Config
from code_01_sensitivity_analysis import (
    generate_random_mask_indices,
    run_single_random_baseline_iteration,
    execute_random_baseline,
    save_random_baseline_results
)

class TestRandomBaseline(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = tempfile.mkdtemp()
        self.config_patcher = patch.dict(os.environ, {'MAX_RAM_THRESHOLD': '7'})
        self.config_patcher.start()
        
        # Mock Config values
        Config.MASK_FRACTION = 0.5
        Config.SAMPLE_SEED = 42
        Config.MAX_RAM_THRESHOLD = 7.0
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.config_patcher.stop()
    
    def test_generate_random_mask_indices(self):
        """Test that random mask indices are generated correctly."""
        param_count = 100
        mask_fraction = 0.5
        
        indices = generate_random_mask_indices(param_count, mask_fraction, seed=42)
        
        self.assertEqual(len(indices), 50)
        self.assertTrue(all(0 <= idx < param_count for idx in indices))
        self.assertEqual(len(set(indices)), 50)  # No duplicates
    
    def test_generate_random_mask_indices_reproducibility(self):
        """Test that same seed produces same indices."""
        param_count = 100
        mask_fraction = 0.5
        
        indices1 = generate_random_mask_indices(param_count, mask_fraction, seed=42)
        indices2 = generate_random_mask_indices(param_count, mask_fraction, seed=42)
        
        self.assertEqual(indices1, indices2)
    
    def test_save_random_baseline_results(self):
        """Test saving random baseline results to CSV."""
        results = [
            {'iteration_id': 0, 'layer_id': 1, 'param_id': 'layer1.param.0', 'faithfulness_score': 0.85},
            {'iteration_id': 0, 'layer_id': 1, 'param_id': 'layer1.param.1', 'faithfulness_score': 0.85},
            {'iteration_id': 1, 'layer_id': 1, 'param_id': 'layer1.param.0', 'faithfulness_score': 0.82},
        ]
        
        output_path = os.path.join(self.test_data_dir, 'random_baseline.csv')
        save_random_baseline_results(results, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]['iteration_id'], '0')
        self.assertEqual(rows[0]['faithfulness_score'], '0.85')
    
    @patch('code_01_sensitivity_analysis.apply_mask_to_layer')
    @patch('code_01_sensitivity_analysis.run_inference_with_masking')
    def test_run_single_random_baseline_iteration(self, mock_inference, mock_mask):
        """Test single random baseline iteration."""
        mock_model = MagicMock()
        mock_masked_model = MagicMock()
        mock_mask.return_value = mock_masked_model
        mock_inference.return_value = [0.85, 0.82, 0.88]
        
        test_dataset = [{'input': 'test1'}, {'input': 'test2'}, {'input': 'test3'}]
        
        mean_score, results = run_single_random_baseline_iteration(
            mock_model,
            'layer1.param',
            3,
            test_dataset,
            0.5,
            0,
            42
        )
        
        self.assertEqual(mean_score, 0.85)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['iteration_id'], 0)
        self.assertEqual(results[0]['faithfulness_score'], 0.85)
    
    @patch('code_01_sensitivity_analysis.run_single_random_baseline_iteration')
    def test_execute_random_baseline(self, mock_iteration):
        """Test executing multiple random baseline iterations."""
        mock_iteration.return_value = (0.85, [{'iteration_id': 0, 'layer_id': 1, 'param_id': 'p0', 'faithfulness_score': 0.85}])
        
        mock_model = MagicMock()
        test_dataset = [{'input': 'test'}]
        
        mean_score, results = execute_random_baseline(
            mock_model,
            'layer1.param',
            10,
            test_dataset,
            0.5,
            num_iterations=3,
            seed=42
        )
        
        self.assertEqual(mean_score, 0.85)
        self.assertEqual(len(results), 3)
        self.assertEqual(mock_iteration.call_count, 3)

if __name__ == '__main__':
    unittest.main()
