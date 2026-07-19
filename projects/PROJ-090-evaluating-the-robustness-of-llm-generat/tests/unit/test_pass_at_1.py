import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.statistics import calculate_pass_at_1, load_results_data

class TestPassAt1:
    """Test pass@1 calculation functionality."""

    def test_calculate_pass_at_1_basic(self):
        """Test basic pass@1 calculation."""
        data = {
            'task_id': ['task1', 'task1', 'task2', 'task2'],
            'perturbation_type': ['original', 'perturbed', 'original', 'perturbed'],
            'result': ['pass', 'fail', 'pass', 'pass']
        }
        df = pd.DataFrame(data)
        
        pass_rates = calculate_pass_at_1(df)
        
        assert 'original' in pass_rates
        assert 'perturbed' in pass_rates
        assert pass_rates['original'] == 1.0  # 2/2 passed
        assert pass_rates['perturbed'] == 0.5  # 1/2 passed

    def test_calculate_pass_at_1_empty(self):
        """Test pass@1 calculation with empty DataFrame."""
        df = pd.DataFrame(columns=['task_id', 'perturbation_type', 'result'])
        pass_rates = calculate_pass_at_1(df)
        assert pass_rates == {}

    def test_calculate_pass_at_1_various_result_formats(self):
        """Test pass@1 calculation with various result formats."""
        data = {
            'task_id': ['task1', 'task1', 'task1', 'task1'],
            'perturbation_type': ['original', 'original', 'original', 'original'],
            'result': ['pass', 'Pass', 'true', '1']
        }
        df = pd.DataFrame(data)
        
        pass_rates = calculate_pass_at_1(df)
        assert pass_rates['original'] == 1.0

    def test_calculate_pass_at_1_no_original(self):
        """Test pass@1 calculation when no original prompts exist."""
        data = {
            'task_id': ['task1', 'task1'],
            'perturbation_type': ['perturbed', 'perturbed'],
            'result': ['pass', 'fail']
        }
        df = pd.DataFrame(data)
        
        pass_rates = calculate_pass_at_1(df)
        assert 'original' not in pass_rates
        assert pass_rates['perturbed'] == 0.5

    def test_calculate_pass_at_1_all_fail(self):
        """Test pass@1 calculation when all results fail."""
        data = {
            'task_id': ['task1', 'task1', 'task2', 'task2'],
            'perturbation_type': ['original', 'original', 'original', 'original'],
            'result': ['fail', 'fail', 'fail', 'fail']
        }
        df = pd.DataFrame(data)
        
        pass_rates = calculate_pass_at_1(df)
        assert pass_rates['original'] == 0.0

    def test_calculate_pass_at_1_all_pass(self):
        """Test pass@1 calculation when all results pass."""
        data = {
            'task_id': ['task1', 'task1', 'task2', 'task2'],
            'perturbation_type': ['original', 'original', 'original', 'original'],
            'result': ['pass', 'pass', 'pass', 'pass']
        }
        df = pd.DataFrame(data)
        
        pass_rates = calculate_pass_at_1(df)
        assert pass_rates['original'] == 1.0

    def test_load_results_data_file_not_found(self):
        """Test load_results_data with non-existent directory."""
        with pytest.raises(FileNotFoundError):
            load_results_data(Path("/nonexistent/path"))

    def test_load_results_data_no_json_files(self, tmp_path):
        """Test load_results_data with empty directory."""
        empty_dir = tmp_path / "empty_results"
        empty_dir.mkdir()
        
        df = load_results_data(empty_dir)
        assert df.empty
        assert list(df.columns) == ['task_id', 'perturbation_type', 'result']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
