import pytest
import json
import os
from code.research.power_analysis import calculate_sample_size, main

class TestPowerAnalysis:
    """Unit tests for power analysis calculations."""

    def test_calculate_sample_size_defaults(self):
        """Test default parameters produce expected output structure."""
        result = calculate_sample_size()
        
        assert result["effect_size"] == 0.25
        assert result["alpha"] == 0.05
        assert result["power"] == 0.80
        assert result["num_groups"] == 3
        assert result["n_per_group"] > 0
        assert result["total_n"] > 0
        assert result["total_n"] == result["n_per_group"] * result["num_groups"]

    def test_calculate_sample_size_custom_parameters(self):
        """Test custom parameters affect the calculation."""
        result = calculate_sample_size(effect_size=0.40, alpha=0.01, power=0.90, k=4)
        
        assert result["effect_size"] == 0.40
        assert result["alpha"] == 0.01
        assert result["power"] == 0.90
        assert result["num_groups"] == 4
        assert result["n_per_group"] > 0
        # Larger effect size should require smaller sample
        assert result["n_per_group"] < calculate_sample_size(effect_size=0.25)["n_per_group"]

    def test_calculate_sample_size_returns_integers(self):
        """Test that sample sizes are returned as integers."""
        result = calculate_sample_size()
        assert isinstance(result["n_per_group"], int)
        assert isinstance(result["total_n"], int)

    def test_main_creates_output_file(self):
        """Test that main() creates the power_calculation.json file."""
        # Run main
        main()
        
        # Check file exists
        output_path = "research/power_calculation.json"
        assert os.path.exists(output_path), f"File {output_path} was not created"
        
        # Check file is valid JSON
        with open(output_path, "r") as f:
            data = json.load(f)
        
        assert "n_per_group" in data
        assert "total_n" in data
        assert data["n_per_group"] > 0

    def test_main_output_matches_calculation(self):
        """Test that main() output matches direct calculation."""
        direct_result = calculate_sample_size()
        main()  # This creates the file
        
        with open("research/power_calculation.json", "r") as f:
            file_result = json.load(f)
        
        assert direct_result["n_per_group"] == file_result["n_per_group"]
        assert direct_result["total_n"] == file_result["total_n"]
