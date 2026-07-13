"""
Tests for power analysis calculations.
"""
import pytest
import json
import os
from code.research.power_analysis import calculate_sample_size

def test_calculate_sample_size_medium_effect():
    """Test calculation with medium effect size (f=0.25)."""
    result = calculate_sample_size(effect_size=0.25, alpha=0.05, power=0.80, k_groups=3)
    
    assert result['effect_size_f'] == 0.25
    assert result['alpha'] == 0.05
    assert result['target_power'] == 0.80
    assert result['k_groups'] == 3
    assert result['required_n_total'] > 0
    assert result['required_n_per_group'] > 0
    assert result['required_n_total'] == result['required_n_per_group'] * 3

def test_calculate_sample_size_large_effect():
    """Test calculation with large effect size (f=0.40)."""
    result = calculate_sample_size(effect_size=0.40, alpha=0.05, power=0.80, k_groups=3)
    
    # Larger effect size should require fewer participants
    result_medium = calculate_sample_size(effect_size=0.25, alpha=0.05, power=0.80, k_groups=3)
    assert result['required_n_total'] < result_medium['required_n_total']

def test_json_output_exists():
    """Test that the power calculation JSON file is generated."""
    # Run the calculation to ensure file exists
    from code.research.power_analysis import main
    main()
    
    output_file = "research/power_calculation.json"
    assert os.path.exists(output_file), f"File {output_file} was not created"
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert 'required_n_total' in data
    assert 'required_n_per_group' in data
    assert data['required_n_total'] >= 150  # Expected for medium effect