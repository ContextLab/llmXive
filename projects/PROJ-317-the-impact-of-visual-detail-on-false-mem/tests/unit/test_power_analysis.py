import json
import pytest
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.stats import calculate_anova_power, main
from config import get_processed_dir

def test_calculate_anova_power_returns_valid_structure():
    """Test that calculate_anova_power returns a dictionary with required keys."""
    result = calculate_anova_power(effect_size=0.25, alpha=0.05, power=0.80)
    
    assert isinstance(result, dict)
    required_keys = [
        'effect_size', 'alpha', 'target_power', 'groups', 
        'required_sample_size_per_group', 'total_required_participants', 'notes'
    ]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"
    
    assert result['effect_size'] == 0.25
    assert result['alpha'] == 0.05
    assert result['target_power'] == 0.80
    assert result['groups'] == 3
    assert result['total_required_participants'] >= 50

def test_calculate_anova_power_with_different_effect_sizes():
    """Test power calculation with different effect sizes."""
    # Larger effect size should require smaller sample size
    result_large = calculate_anova_power(effect_size=0.40)
    # Smaller effect size should require larger sample size
    result_small = calculate_anova_power(effect_size=0.10)
    
    assert result_large['total_required_participants'] < result_small['total_required_participants']

def test_main_halts_when_n_less_than_50():
    """Test that main() raises an error if calculated N < 50."""
    # Mock calculate_anova_power to return a value < 50
    mock_result = {
        'effect_size': 0.25,
        'alpha': 0.05,
        'target_power': 0.80,
        'groups': 3,
        'required_sample_size_per_group': 10,
        'total_required_participants': 30, # Less than 50
        'notes': 'Test'
    }
    
    with patch('analysis.stats.calculate_anova_power', return_value=mock_result):
        with pytest.raises(ValueError) as excinfo:
            main()
        
        assert "constraint violated" in str(excinfo.value).lower()
        assert "less than the minimum threshold of 50" in str(excinfo.value).lower()

def test_main_saves_file_when_n_ge_50(tmp_path):
    """Test that main() saves the file when N >= 50."""
    mock_result = {
        'effect_size': 0.25,
        'alpha': 0.05,
        'target_power': 0.80,
        'groups': 3,
        'required_sample_size_per_group': 20,
        'total_required_participants': 60,
        'notes': 'Test'
    }
    
    # Mock get_processed_dir to use tmp_path
    with patch('analysis.stats.calculate_anova_power', return_value=mock_result):
        with patch('analysis.stats.get_processed_dir', return_value=tmp_path):
            main()
            
            output_file = tmp_path / "power_report.json"
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data['total_required_participants'] == 60