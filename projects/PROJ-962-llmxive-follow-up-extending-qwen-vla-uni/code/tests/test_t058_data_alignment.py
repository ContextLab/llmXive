"""
Unit tests for T058: Paired T-Test Data Alignment.

This module verifies that the simulation script enforces the "paired" nature
of t-tests by ensuring prompt IDs are identical across all baselines.
"""
import unittest
import sys
import os
import tempfile
import json
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.seeds import set_global_seed

class TestDataAlignment(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.base_prompts = pd.DataFrame({
            'prompt_id': ['p1', 'p2', 'p3', 'p4', 'p5'],
            'text_instruction': ['task1', 'task2', 'task3', 'task4', 'task5']
        })
        self.vla_actions = [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]]
        self.random_actions = [[11, 12], [13, 14], [15, 16], [17, 18], [19, 20]]
        self.nn_actions = [[21, 22], [23, 24], [25, 26], [27, 28], [29, 30]]
        
    def test_alignment_success(self):
        """Test that alignment verification passes when data is consistent."""
        from code.simulate_eval import verify_data_alignment
        
        # This should not raise
        result = verify_data_alignment(
            self.base_prompts, 
            self.vla_actions, 
            self.random_actions, 
            self.nn_actions
        )
        self.assertTrue(result)
        
    def test_alignment_failure_vla_mismatch(self):
        """Test that alignment verification fails when VLA actions count mismatches."""
        from code.simulate_eval import verify_data_alignment
        
        short_vla = self.vla_actions[:3] # Only 3 items
        
        with self.assertRaises(RuntimeError) as context:
            verify_data_alignment(
                self.base_prompts, 
                short_vla, 
                self.random_actions, 
                self.nn_actions
            )
        
        self.assertIn("Data Alignment Failed", str(context.exception))
        self.assertIn("VLA Proxy actions length", str(context.exception))
        
    def test_alignment_failure_random_mismatch(self):
        """Test that alignment verification fails when Random actions count mismatches."""
        from code.simulate_eval import verify_data_alignment
        
        short_random = self.random_actions[:2]
        
        with self.assertRaises(RuntimeError) as context:
            verify_data_alignment(
                self.base_prompts, 
                self.vla_actions, 
                short_random, 
                self.nn_actions
            )
        
        self.assertIn("Data Alignment Failed", str(context.exception))
        self.assertIn("Random Baseline actions length", str(context.exception))
        
    def test_alignment_failure_nn_mismatch(self):
        """Test that alignment verification fails when Non-Neural actions count mismatches."""
        from code.simulate_eval import verify_data_alignment
        
        short_nn = self.nn_actions[:4]
        
        with self.assertRaises(RuntimeError) as context:
            verify_data_alignment(
                self.base_prompts, 
                self.vla_actions, 
                self.random_actions, 
                short_nn
            )
        
        self.assertIn("Data Alignment Failed", str(context.exception))
        self.assertIn("Non-Neural actions length", str(context.exception))

if __name__ == '__main__':
    unittest.main()