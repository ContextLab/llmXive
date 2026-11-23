"""
Unit tests for power analysis functionality in code/eval/stats.py
"""
import pytest
import json
import os
import sys
from pathlib import Path
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eval.stats import run_power_analysis, RESULTS_DIR

class TestPowerAnalysis:
    """Test cases for power analysis calculations."""
    
    def test_power_analysis_calculates_required_sample_size(self):
        """Test that power analysis correctly calculates required sample size."""
        result = run_power_analysis(alpha=0.05, effect_size=0.5, power=0.8)
        
        assert 'required_sample_size' in result
        assert result['required_sample_size'] > 0
        assert isinstance(result['required_sample_size'], int)
        
    def test_power_analysis_returns_valid_status(self):
        """Test that power analysis returns a valid status string."""
        result = run_power_analysis(alpha=0.05, effect_size=0.5, power=0.8)
        
        assert 'status' in result
        assert result['status'] in ['ADEQUATE', 'UNDERPOWERED']
        
    def test_power_analysis_saves_to_json(self):
        """Test that power analysis results are saved to JSON file."""
        result = run_power_analysis(alpha=0.05, effect_size=0.5, power=0.8)
        
        output_path = RESULTS_DIR / "power_analysis.json"
        assert output_path.exists(), "Power analysis JSON file not created"
        
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
            
        assert saved_data['alpha'] == 0.05
        assert saved_data['effect_size'] == 0.5
        assert saved_data['target_power'] == 0.8
        
    def test_power_analysis_with_different_parameters(self):
        """Test power analysis with different alpha and effect size."""
        result = run_power_analysis(alpha=0.01, effect_size=0.8, power=0.9)
        
        assert result['alpha'] == 0.01
        assert result['effect_size'] == 0.8
        assert result['target_power'] == 0.9
        assert result['required_sample_size'] > 0
        
    def test_power_analysis_structure(self):
        """Test that power analysis result has all required fields."""
        result = run_power_analysis(alpha=0.05, effect_size=0.5, power=0.8)
        
        required_fields = [
            'alpha', 'effect_size', 'target_power',
            'required_sample_size', 'current_sample_size',
            'current_power', 'status', 'note'
        ]
        
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
