"""
Unit tests for T013b: Sample Size Calculation for LLM Consensus Validation.
"""
import pytest
import json
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from metrics import calculate_dynamic_sample_size, calculate_sample_config

class TestT013bSampleSizeCalculation:
    """Tests for sample size calculation logic."""

    def test_sample_size_minimum_threshold(self):
        """Test that sample size is at least the minimum threshold (10)."""
        # Small flagged count should return minimum threshold
        result = calculate_dynamic_sample_size(flagged_count=50, min_threshold=10, percentage=0.05)
        # 5% of 50 = 2.5 -> 2, but min is 10
        assert result == 10

    def test_sample_size_percentage(self):
        """Test that sample size is calculated as percentage when above minimum."""
        # Large flagged count should use percentage
        result = calculate_dynamic_sample_size(flagged_count=1000, min_threshold=10, percentage=0.05)
        # 5% of 1000 = 50, which is > 10
        assert result == 50

    def test_sample_size_zero_flagged(self):
        """Test that sample size is 0 when flagged count is 0."""
        result = calculate_dynamic_sample_size(flagged_count=0, min_threshold=10, percentage=0.05)
        assert result == 0

    def test_sample_size_exact_boundary(self):
        """Test boundary where percentage equals minimum threshold."""
        # 5% of 200 = 10, which equals min_threshold
        result = calculate_dynamic_sample_size(flagged_count=200, min_threshold=10, percentage=0.05)
        assert result == 10

    def test_sample_config_skip_validation_zero(self):
        """Test that skip_validation is True when sample size is 0."""
        config = calculate_sample_config(flagged_count=0)
        assert config["sample_size"] == 0
        assert config["skip_validation"] is True
        assert config["minimum_threshold"] == 10
        assert config["percentage"] == 0.05

    def test_sample_config_skip_validation_false(self):
        """Test that skip_validation is False when sample size > 0."""
        config = calculate_sample_config(flagged_count=100)
        assert config["sample_size"] > 0
        assert config["skip_validation"] is False

    def test_sample_config_schema(self):
        """Test that sample config has the correct schema."""
        config = calculate_sample_config(flagged_count=500)
        assert "sample_size" in config
        assert "minimum_threshold" in config
        assert "percentage" in config
        assert "skip_validation" in config
        assert isinstance(config["sample_size"], int)
        assert isinstance(config["minimum_threshold"], int)
        assert isinstance(config["percentage"], float)
        assert isinstance(config["skip_validation"], bool)

    def test_run_sample_size_calculation_integration(self):
        """Integration test for the full sample size calculation flow."""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        try:
            input_file = os.path.join(temp_dir, "flagged_pairs_count.json")
            output_file = os.path.join(temp_dir, "sample_config.json")
            
            # Write mock input data
            input_data = {
                "wasted_count": 200,
                "total_pairs": 1000,
                "wasted_ratio": 0.2
            }
            with open(input_file, 'w') as f:
                json.dump(input_data, f)
            
            # Run calculation
            from metrics import run_sample_size_calculation
            result = run_sample_size_calculation(input_file, output_file)
            
            # Verify output file exists
            assert os.path.exists(output_file)
            
            # Verify output content
            with open(output_file, 'r') as f:
                output_data = json.load(f)
            
            assert output_data["sample_size"] == 10  # max(10, 0.05*200=10)
            assert output_data["skip_validation"] is False
            
        finally:
            # Cleanup
            shutil.rmtree(temp_dir)