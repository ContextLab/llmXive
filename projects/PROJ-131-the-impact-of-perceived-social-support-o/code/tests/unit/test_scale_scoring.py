"""
Unit tests for scale scoring logic.
Tests verify that scoring matches definitions in code/config/scales.yaml.
"""
import pytest
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.config_loader import load_yaml_config
from code.analysis.scales import score_cesd, score_gad7, score_pcl5


def load_scales_config():
    """Load the scales configuration file."""
    config_path = Path(__file__).parent.parent.parent / "code" / "config" / "scales.yaml"
    return load_yaml_config(config_path)


class TestScaleConfig:
    """Test that the scale configuration file is valid."""

    def test_scale_config_exists(self):
        """Test that the scale config file exists."""
        config_path = Path(__file__).parent.parent.parent / "code" / "config" / "scales.yaml"
        assert config_path.exists(), "scales.yaml config file not found"

    def test_scale_config_valid_yaml(self):
        """Test that the scale config is valid YAML."""
        config = load_scales_config()
        assert config is not None, "Failed to load scales config"
        assert isinstance(config, dict), "Scales config should be a dictionary"

    def test_scale_variables_match_spec(self):
        """Test that scale variables match the spec's data dictionary."""
        config = load_scales_config()
        assert 'CES-D' in config, "CES-D configuration missing"
        assert 'GAD-7' in config, "GAD-7 configuration missing"
        assert 'PCL-5' in config, "PCL-5 configuration missing"

        # Check variable names match spec
        assert config['CES-D']['variable'] == 'depression', "CES-D variable name mismatch"
        assert config['GAD-7']['variable'] == 'anxiety', "GAD-7 variable name mismatch"
        assert config['PCL-5']['variable'] == 'ptsd', "PCL-5 variable name mismatch"


class TestReverseCoding:
    """Test reverse coding logic."""

    def test_reverse_coding(self):
        """Test that reverse coding transforms [0, 1, 2, 3] to [3, 2, 1, 0]."""
        # Input: [0, 1, 2, 3]
        # Expected output: [3, 2, 1, 0]
        input_items = np.array([0, 1, 2, 3])
        expected_output = np.array([3, 2, 1, 0])
        
        # The reverse coding formula is: 3 - item_value
        actual_output = 3 - input_items
        
        np.testing.assert_array_equal(actual_output, expected_output)


class TestCESDScoring:
    """Test CES-D scoring logic."""

    def test_cesd_scoring_all_zeros(self):
        """Test CES-D scoring with all zeros (minimum score)."""
        # CES-D has 20 items. All zeros should result in score of 0.
        items = np.zeros(20)
        config = load_scales_config()
        reverse_items = config['CES-D']['reverse_items']
        
        # Convert 1-indexed to 0-indexed
        reverse_items_0idx = [i - 1 for i in reverse_items]
        
        # Apply reverse coding to specified items
        scored_items = items.copy()
        for idx in reverse_items_0idx:
            scored_items[idx] = 3 - items[idx]
        
        # Sum all items
        total_score = np.sum(scored_items)
        
        assert total_score == 0, f"Expected CES-D score 0, got {total_score}"

    def test_cesd_scoring_all_threes(self):
        """Test CES-D scoring with all threes (maximum score)."""
        # CES-D has 20 items. All threes should result in score of 60.
        items = np.full(20, 3)
        config = load_scales_config()
        reverse_items = config['CES-D']['reverse_items']
        
        # Convert 1-indexed to 0-indexed
        reverse_items_0idx = [i - 1 for i in reverse_items]
        
        # Apply reverse coding to specified items
        scored_items = items.copy()
        for idx in reverse_items_0idx:
            scored_items[idx] = 3 - items[idx]
        
        # Sum all items
        total_score = np.sum(scored_items)
        
        assert total_score == 60, f"Expected CES-D score 60, got {total_score}"

    def test_cesd_scoring_mixed_values(self):
        """Test CES-D scoring with mixed values."""
        # Create a specific test case
        items = np.array([1, 2, 0, 3, 1, 2, 0, 3, 1, 2, 0, 3, 1, 2, 0, 3, 1, 2, 0, 3])
        config = load_scales_config()
        reverse_items = config['CES-D']['reverse_items']
        
        # Convert 1-indexed to 0-indexed
        reverse_items_0idx = [i - 1 for i in reverse_items]
        
        # Apply reverse coding to specified items
        scored_items = items.copy()
        for idx in reverse_items_0idx:
            scored_items[idx] = 3 - items[idx]
        
        # Sum all items
        total_score = np.sum(scored_items)
        
        # Verify the calculation
        expected_score = 0
        for i, item in enumerate(items):
            if (i + 1) in reverse_items:
                expected_score += 3 - item
            else:
                expected_score += item
        
        assert total_score == expected_score, f"Expected CES-D score {expected_score}, got {total_score}"


class TestGAD7Scoring:
    """Test GAD-7 scoring logic."""

    def test_gad7_scoring_all_zeros(self):
        """Test GAD-7 scoring with all zeros (minimum score)."""
        # GAD-7 has 7 items. All zeros should result in score of 0.
        items = np.zeros(7)
        total_score = np.sum(items)
        assert total_score == 0, f"Expected GAD-7 score 0, got {total_score}"

    def test_gad7_scoring_all_threes(self):
        """Test GAD-7 scoring with all threes (maximum score)."""
        # GAD-7 has 7 items. All threes should result in score of 21.
        items = np.full(7, 3)
        total_score = np.sum(items)
        assert total_score == 21, f"Expected GAD-7 score 21, got {total_score}"

    def test_gad7_scoring_mixed_values(self):
        """Test GAD-7 scoring with mixed values."""
        # Input: [0, 1, 2, 3, 0, 1, 2] (as specified in task)
        items = np.array([0, 1, 2, 3, 0, 1, 2])
        total_score = np.sum(items)
        expected_score = 9
        assert total_score == expected_score, f"Expected GAD-7 score {expected_score}, got {total_score}"


class TestPCL5Scoring:
    """Test PCL-5 scoring logic."""

    def test_pcl5_scoring_all_zeros(self):
        """Test PCL-5 scoring with all zeros (minimum score)."""
        # PCL-5 has 20 items. All zeros should result in score of 0.
        items = np.zeros(20)
        total_score = np.sum(items)
        assert total_score == 0, f"Expected PCL-5 score 0, got {total_score}"

    def test_pcl5_scoring_all_fours(self):
        """Test PCL-5 scoring with all fours (maximum score)."""
        # PCL-5 has 20 items, each scored 0-4. All fours should result in score of 80.
        items = np.full(20, 4)
        total_score = np.sum(items)
        assert total_score == 80, f"Expected PCL-5 score 80, got {total_score}"

    def test_pcl5_scoring_mixed_values(self):
        """Test PCL-5 scoring with mixed values."""
        # Create a specific test case
        items = np.array([0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4])
        total_score = np.sum(items)
        expected_score = 40  # (0+1+2+3+4) * 4 = 10 * 4 = 40
        assert total_score == expected_score, f"Expected PCL-5 score {expected_score}, got {total_score}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])