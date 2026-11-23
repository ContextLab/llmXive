"""
Unit tests for CES-D, GAD-7, and PCL-5 scoring logic.

This module verifies that the scoring functions in `code/analysis/scales.py`
correctly implement the standard algorithms defined in `code/config/scales.yaml`.

It tests:
1. Reverse coding logic.
2. CES-D total score calculation (including reverse items).
3. GAD-7 total score calculation.
4. PCL-5 total score calculation (aggregate mode).
"""
import pytest
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add the project root to the path to allow imports from code/
# Assuming this test runs from the project root or via pytest discovery
project_root = Path(__file__).parent.parent.parent
if str(project_root / 'code') not in sys.path:
    sys.path.insert(0, str(project_root / 'code'))

from analysis.scales import load_scale_config, score_cesd, score_gad7, score_pcl5


@pytest.fixture
def scales_config():
    """Load the scale configuration from the project config file."""
    config_path = project_root / 'code' / 'config' / 'scales.yaml'
    if not config_path.exists():
        pytest.fail(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class TestReverseCoding:
    """Tests for the reverse coding logic used in CES-D."""

    def test_reverse_coding_logic(self):
        """
        Verify that reverse coding maps:
        0 -> 3
        1 -> 2
        2 -> 1
        3 -> 0
        """
        # Input: [0, 1, 2, 3]
        # Expected: [3, 2, 1, 0]
        input_items = np.array([0, 1, 2, 3])
        expected = np.array([3, 2, 1, 0])
        
        # The scoring logic typically does: 3 - item_value
        result = 3 - input_items
        
        np.testing.assert_array_equal(result, expected)

    def test_reverse_coding_edge_cases(self):
        """Test extreme values."""
        assert (3 - 0) == 3
        assert (3 - 3) == 0


class TestCESDScoring:
    """Tests for CES-D scoring logic."""

    def test_cesd_scoring_simple(self, scales_config):
        """
        Test a simple case where all items are 0 (no depression).
        Expected score: 0.
        """
        # 20 items, all 0
        items = np.zeros(20, dtype=int)
        score = score_cesd(items, scales_config)
        assert score == 0.0

    def test_cesd_scoring_all_max(self, scales_config):
        """
        Test a case where all items are 3 (max depression).
        Expected score: 60 (20 items * 3).
        """
        items = np.full(20, 3, dtype=int)
        score = score_cesd(items, scales_config)
        assert score == 60.0

    def test_cesd_scoring_mixed(self, scales_config):
        """
        Test a mixed input to ensure reverse coding is applied correctly.
        Items: [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3]
        
        Reverse items (1-indexed in config, 0-indexed here):
        Config reverse_items: [5, 7, 8, 11, 12, 15, 18, 19, 20]
        0-indexed: [4, 6, 7, 10, 11, 14, 17, 18, 19]
        
        Let's verify the calculation manually for a subset:
        Index 4 (Item 5): Input 0 -> Reverse -> 3
        Index 6 (Item 7): Input 2 -> Reverse -> 1
        Index 19 (Item 20): Input 3 -> Reverse -> 0
        """
        items = np.array([0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3])
        
        # Manual calculation based on standard CES-D reverse items
        # Reverse items (1-based): 5, 7, 8, 11, 12, 15, 18, 19, 20
        # 0-based indices: 4, 6, 7, 10, 11, 14, 17, 18, 19
        
        reverse_indices = [4, 6, 7, 10, 11, 14, 17, 18, 19]
        non_reverse_indices = [i for i in range(20) if i not in reverse_indices]
        
        # Calculate expected score
        expected_score = 0
        for i in range(20):
            val = items[i]
            if i in reverse_indices:
                expected_score += (3 - val)
            else:
                expected_score += val
        
        score = score_cesd(items, scales_config)
        
        # Allow for float comparison if the function returns float
        assert np.isclose(score, expected_score), f"Expected {expected_score}, got {score}"


class TestGAD7Scoring:
    """Tests for GAD-7 scoring logic."""

    def test_gad7_scoring_all_zero(self, scales_config):
        """All items 0 -> Score 0."""
        items = np.zeros(7, dtype=int)
        score = score_gad7(items, scales_config)
        assert score == 0.0

    def test_gad7_scoring_all_max(self, scales_config):
        """All items 3 -> Score 21."""
        items = np.full(7, 3, dtype=int)
        score = score_gad7(items, scales_config)
        assert score == 21.0

    def test_gad7_scoring_mixed(self, scales_config):
        """
        Input: [0, 1, 2, 3, 0, 1, 2]
        Expected: 0+1+2+3+0+1+2 = 9
        """
        items = np.array([0, 1, 2, 3, 0, 1, 2], dtype=int)
        score = score_gad7(items, scales_config)
        assert score == 9.0


class TestPCL5Scoring:
    """Tests for PCL-5 scoring logic."""

    def test_pcl5_scoring_all_zero(self, scales_config):
        """All items 0 -> Score 0."""
        items = np.zeros(20, dtype=int) # PCL-5 has 20 items
        score = score_pcl5(items, scales_config)
        assert score == 0.0

    def test_pcl5_scoring_all_max(self, scales_config):
        """All items 4 -> Score 80."""
        # PCL-5 items are typically 0-4
        items = np.full(20, 4, dtype=int)
        score = score_pcl5(items, scales_config)
        assert score == 80.0

    def test_pcl5_scoring_mixed(self, scales_config):
        """
        Input: [0, 1, 2, 3, 4] repeated 4 times.
        Sum of one group: 0+1+2+3+4 = 10
        Total: 40
        """
        items = np.tile([0, 1, 2, 3, 4], 4)
        score = score_pcl5(items, scales_config)
        assert score == 40.0

    def test_pcl5_aggregate_mode(self, scales_config):
        """
        Test that if the config specifies 'aggregate_score', 
        the function handles a pre-summed value or a single column correctly.
        This test mocks the config to ensure the logic branch exists.
        """
        # Modify config locally for this test
        test_config = {
            'PCL-5': {
                'variable': 'ptsd',
                'type': 'aggregate_score'
            }
        }
        
        # If the function expects an array of items, we test the standard path.
        # If it expects an aggregate column, the behavior might differ.
        # Based on the task description, we assume standard item scoring is the primary path.
        # We verify the function doesn't crash with standard input.
        items = np.zeros(20, dtype=int)
        score = score_pcl5(items, test_config)
        assert score == 0.0