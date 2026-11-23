import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from evaluation.falsifiability_check import (
    calculate_performance_drop, 
    load_json_file, 
    load_yaml_config
)

class TestCalculatePerformanceDrop:
    def test_normal_drop(self):
        """Test calculation with normal positive values."""
        learned = 10.0
        static = 9.0
        drop = calculate_performance_drop(learned, static)
        # (10 - 9) / 10 = 0.1
        assert abs(drop - 0.1) < 1e-6

    def test_no_drop(self):
        """Test calculation when static equals learned."""
        learned = 5.0
        static = 5.0
        drop = calculate_performance_drop(learned, static)
        assert abs(drop - 0.0) < 1e-6

    def test_improvement_negative_drop(self):
        """Test calculation when static is better (lower perplexity)."""
        learned = 10.0
        static = 8.0
        drop = calculate_performance_drop(learned, static)
        # (10 - 8) / 10 = 0.2
        assert abs(drop - 0.2) < 1e-6

    def test_zero_division_guard(self):
        """Test that zero-division guard raises error for near-zero learned mean."""
        learned = 1e-7  # Below 1e-6 threshold
        static = 0.0
        with pytest.raises(ZeroDivisionError):
            calculate_performance_drop(learned, static)

    def test_exact_threshold_boundary(self):
        """Test calculation exactly at threshold boundary."""
        learned = 100.0
        static = 95.0
        # Drop = (100-95)/100 = 0.05
        drop = calculate_performance_drop(learned, static)
        assert abs(drop - 0.05) < 1e-6

class TestLoadJsonFile:
    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file."""
        test_file = tmp_path / "test.json"
        data = {"key": "value", "number": 42}
        with open(test_file, 'w') as f:
            json.dump(data, f)
        
        loaded = load_json_file(str(test_file))
        assert loaded == data

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_json_file(str(tmp_path / "nonexistent.json"))

class TestLoadYamlConfig:
    def test_load_simple_yaml(self, tmp_path):
        """Test loading a simple YAML config file."""
        config_file = tmp_path / "config.yaml"
        content = """
        drop_threshold: 0.01
        metric_name: "test_metric"
        """
        with open(config_file, 'w') as f:
            f.write(content)
        
        config = load_yaml_config(str(config_file))
        assert config['drop_threshold'] == 0.01
        assert config['metric_name'] == "test_metric"

    def test_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing config."""
        with pytest.raises(FileNotFoundError):
            load_yaml_config(str(tmp_path / "missing.yaml"))