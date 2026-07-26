import json
import os
import tempfile
from pathlib import Path
import numpy as np
import pytest
from scipy import stats

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.statistics import (
    load_gradient_norms,
    compare_gradient_stability,
    compare_ablation_results,
    calculate_scaling_exponent
)

class TestLoadGradientNorms:
    def test_load_valid_file(self, tmp_path):
        """Test loading gradient norms from a valid JSON file."""
        test_data = {
            "steps": [
                {"step": 0, "norm": 1.0},
                {"step": 1, "norm": 0.8},
                {"step": 2, "norm": 0.9}
            ]
        }
        
        file_path = tmp_path / "gradient_norms.json"
        with open(file_path, 'w') as f:
            json.dump(test_data, f)
        
        norms = load_gradient_norms(str(file_path))
        
        assert norms == [1.0, 0.8, 0.9]
        assert len(norms) == 3

    def test_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_gradient_norms(str(tmp_path / "nonexistent.json"))

    def test_invalid_format(self, tmp_path):
        """Test that ValueError is raised for invalid format."""
        file_path = tmp_path / "invalid.json"
        with open(file_path, 'w') as f:
            json.dump({"data": []}, f)
        
        with pytest.raises(ValueError):
            load_gradient_norms(str(file_path))

class TestCompareGradientStability:
    def test_identical_distributions(self, tmp_path):
        """Test KS test with identical distributions."""
        # Create identical data
        baseline_data = {"steps": [{"step": i, "norm": 1.0 + 0.1 * i % 1} for i in range(100)]}
        micro_data = {"steps": [{"step": i, "norm": 1.0 + 0.1 * i % 1} for i in range(100)]}
        
        baseline_file = tmp_path / "baseline.json"
        micro_file = tmp_path / "microcircuit.json"
        output_file = tmp_path / "output.json"
        
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f)
        with open(micro_file, 'w') as f:
            json.dump(micro_data, f)
        
        result = compare_gradient_stability(
            str(baseline_file),
            str(micro_file),
            str(output_file)
        )
        
        assert "ks_statistic" in result
        assert "p_value" in result
        assert "stable" in result
        
        # For identical distributions, p-value should be high (stable=True)
        assert result["stable"] is True
        assert result["ks_statistic"] == 0.0  # Identical distributions

    def test_different_distributions(self, tmp_path):
        """Test KS test with different distributions."""
        # Create different data
        baseline_data = {"steps": [{"step": i, "norm": 1.0} for i in range(100)]}
        micro_data = {"steps": [{"step": i, "norm": 2.0} for i in range(100)]}
        
        baseline_file = tmp_path / "baseline.json"
        micro_file = tmp_path / "microcircuit.json"
        output_file = tmp_path / "output.json"
        
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f)
        with open(micro_file, 'w') as f:
            json.dump(micro_data, f)
        
        result = compare_gradient_stability(
            str(baseline_file),
            str(micro_file),
            str(output_file)
        )
        
        assert result["ks_statistic"] > 0.0
        # With completely different values, p-value should be low
        assert result["p_value"] < 0.05
        assert result["stable"] is False

    def test_output_file_created(self, tmp_path):
        """Test that output file is created."""
        baseline_data = {"steps": [{"step": i, "norm": 1.0} for i in range(10)]}
        micro_data = {"steps": [{"step": i, "norm": 1.1} for i in range(10)]}
        
        baseline_file = tmp_path / "baseline.json"
        micro_file = tmp_path / "microcircuit.json"
        output_file = tmp_path / "output.json"
        
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f)
        with open(micro_file, 'w') as f:
            json.dump(micro_data, f)
        
        compare_gradient_stability(
            str(baseline_file),
            str(micro_file),
            str(output_file)
        )
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        assert "ks_statistic" in result
        assert "p_value" in result
        assert "stable" in result

    def test_empty_gradient_list(self, tmp_path):
        """Test that ValueError is raised for empty gradient list."""
        baseline_data = {"steps": []}
        micro_data = {"steps": [{"step": 0, "norm": 1.0}]}
        
        baseline_file = tmp_path / "baseline.json"
        micro_file = tmp_path / "microcircuit.json"
        output_file = tmp_path / "output.json"
        
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f)
        with open(micro_file, 'w') as f:
            json.dump(micro_data, f)
        
        with pytest.raises(ValueError):
            compare_gradient_stability(
                str(baseline_file),
                str(micro_file),
                str(output_file)
            )