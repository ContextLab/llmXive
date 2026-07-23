"""
Unit tests for the power analysis module.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analysis.power import (
    load_filtered_tasks,
    calculate_achieved_power,
    run_power_analysis
)

class TestLoadFilteredTasks:
    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid filtered tasks CSV."""
        csv_path = tmp_path / "filtered_tasks.csv"
        data = {
            'task_id': ['t1', 't2', 't3'],
            'raw_prompt': ['p1', 'p2', 'p3'],
            'progressive_constraints': [['c1'], ['c2', 'c3'], ['c4']],
            'constraint_count': [1, 2, 1]
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        df = load_filtered_tasks(csv_path)
        
        assert len(df) == 3
        assert 'task_id' in df.columns
        assert 'constraint_count' in df.columns
    
    def test_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        csv_path = tmp_path / "nonexistent.csv"
        
        with pytest.raises(FileNotFoundError):
            load_filtered_tasks(csv_path)
    
    def test_missing_columns(self, tmp_path):
        """Test that ValueError is raised for missing required columns."""
        csv_path = tmp_path / "filtered_tasks.csv"
        data = {
            'task_id': ['t1', 't2'],
            'raw_prompt': ['p1', 'p2']
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        with pytest.raises(ValueError):
            load_filtered_tasks(csv_path)

class TestCalculateAchievedPower:
    def test_power_calculation(self):
        """Test that power is calculated correctly for a known sample size."""
        sample_size = 100
        effect_size = 0.15
        alpha = 0.05
        groups = 2
        
        power = calculate_achieved_power(sample_size, effect_size, alpha, groups)
        
        assert 0 <= power <= 1
        # For a sample size of 100 and effect size of 0.15, power should be reasonable (> 0.5)
        assert power > 0.5
    
    def test_small_sample_size(self):
        """Test power calculation with a small sample size."""
        sample_size = 10
        effect_size = 0.15
        alpha = 0.05
        groups = 2
        
        power = calculate_achieved_power(sample_size, effect_size, alpha, groups)
        
        assert 0 <= power <= 1
        # Power should be low for small sample sizes
        assert power < 0.5
    
    def test_large_effect_size(self):
        """Test power calculation with a large effect size."""
        sample_size = 50
        effect_size = 0.5  # Large effect
        alpha = 0.05
        groups = 2
        
        power = calculate_achieved_power(sample_size, effect_size, alpha, groups)
        
        assert 0 <= power <= 1
        # Power should be high for large effect sizes
        assert power > 0.8

class TestRunPowerAnalysis:
    def test_run_power_analysis_writes_output(self, tmp_path):
        """Test that run_power_analysis writes the output JSON file."""
        # Create a temporary input CSV
        input_path = tmp_path / "filtered_tasks.csv"
        data = {
            'task_id': [f't{i}' for i in range(50)],
            'raw_prompt': [f'p{i}' for i in range(50)],
            'progressive_constraints': [['c1'] for _ in range(50)],
            'constraint_count': [1 for _ in range(50)]
        }
        pd.DataFrame(data).to_csv(input_path, index=False)
        
        output_path = tmp_path / "power_report.json"
        
        result = run_power_analysis(
            input_path=input_path,
            output_path=output_path,
            effect_size=0.15,
            alpha=0.05,
            groups=2
        )
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            saved_result = json.load(f)
        
        assert 'calculated_power' in saved_result
        assert 'effect_size' in saved_result
        assert 'sample_size' in saved_result
        assert 'groups' in saved_result
        assert saved_result['sample_size'] == 50
        assert saved_result['effect_size'] == 0.15
        assert saved_result['groups'] == 2
        assert 0 <= saved_result['calculated_power'] <= 1