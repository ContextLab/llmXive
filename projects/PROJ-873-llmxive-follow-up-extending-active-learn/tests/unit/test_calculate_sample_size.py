"""
Unit tests for T013c: calculate_sample_size.py
"""
import os
import sys
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from metrics import calculate_dynamic_sample_size

class TestCalculateDynamicSampleSize:
    """Tests for the calculate_dynamic_sample_size function."""

    def test_zero_flagged(self):
        """Test with zero flagged pairs."""
        assert calculate_dynamic_sample_size(0) == 0

    def test_small_count_below_minimum(self):
        """Test with a small count that results in a value below minimum."""
        # 5 * 0.2 = 1, but min is 20
        assert calculate_dynamic_sample_size(5) == 20

    def test_large_count_capped_at_max(self):
        """Test with a large count that results in a value above maximum."""
        # 10000 * 0.2 = 2000, but max is 1000
        assert calculate_dynamic_sample_size(10000) == 1000

    def test_normal_count(self):
        """Test with a normal count that falls between min and max."""
        # 100 * 0.2 = 20
        assert calculate_dynamic_sample_size(100) == 20

    def test_custom_parameters(self):
        """Test with custom min/max/percentage."""
        # 100 * 0.5 = 50, min=10, max=40 -> should be 40
        assert calculate_dynamic_sample_size(100, min_sample=10, max_sample=40, percentage=0.5) == 40

class TestCalculateSampleSizeScript:
    """Tests for the calculate_sample_size.py script execution."""

    def test_script_execution(self, tmp_path):
        """Test that the script runs and produces the correct output file."""
        # Create input file
        input_file = tmp_path / "flagged_pairs_count.json"
        input_data = {"total_flagged_count": 100}
        with open(input_file, 'w') as f:
            json.dump(input_data, f)

        output_file = tmp_path / "sample_config.json"

        # Mock get_config to return a simple object with max_sample_size
        class MockConfig:
            max_sample_size = 1000

        with patch('calculate_sample_size.get_config', return_value=MockConfig()):
            # Import and run main
            from calculate_sample_size import main
            import argparse
            
            # We need to simulate the arguments
            with patch('sys.argv', ['calculate_sample_size.py', '--input', str(input_file), '--output', str(output_file)]):
                main()

        # Verify output
        assert output_file.exists()
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        assert result["total_flagged_count"] == 100
        assert result["sample_size"] == 20
        assert result["calculation_method"] == "dynamic_percentage_capped"