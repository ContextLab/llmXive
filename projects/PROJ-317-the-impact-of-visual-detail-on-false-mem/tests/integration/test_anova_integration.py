import json
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.anova import load_false_memory_data, run_anova, save_results, main
from config import get_data_dir

@pytest.fixture
def mock_data_file(tmp_path):
    """Create a mock false_memory_rates.csv file."""
    data_dir = tmp_path / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    data_file = data_dir / "false_memory_rates.csv"
    
    # Create realistic mock data for Repeated-Measures ANOVA
    # 10 participants, 3 conditions each
    data = []
    for p_id in range(1, 11):
        for condition in ['Baseline', 'Enhanced', 'Reduced']:
            # Simulate some variation
            if condition == 'Baseline':
                rate = 0.25
            elif condition == 'Enhanced':
                rate = 0.15  # Lower false memory with more detail
            else:  # Reduced
                rate = 0.35  # Higher false memory with less detail
            
            data.append({
                'participant_id': f'P{p_id:03d}',
                'condition': condition,
                'false_memory_rate': rate
            })
    
    df = pd.DataFrame(data)
    df.to_csv(data_file, index=False)
    return data_file

@pytest.fixture
def mock_power_gate(tmp_path):
    """Create a mock power_gate_passed.txt file."""
    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    gate_file = analysis_dir / "power_gate_passed.txt"
    gate_file.write_text("Power analysis passed. Gate approved.\n")
    return gate_file

def test_load_false_memory_data(mock_data_file, mock_power_gate, tmp_path):
    """Test that load_false_memory_data correctly reads the CSV."""
    # Temporarily override get_data_dir to use tmp_path
    import config
    original_get_data_dir = config.get_data_dir
    config.get_data_dir = lambda: tmp_path
    
    try:
        df = load_false_memory_data()
        assert df is not None
        assert 'participant_id' in df.columns
        assert 'condition' in df.columns
        assert 'false_memory_rate' in df.columns
        assert len(df) == 30  # 10 participants * 3 conditions
    finally:
        config.get_data_dir = original_get_data_dir

def test_run_anova(mock_data_file, mock_power_gate, tmp_path):
    """Test that run_anova produces valid results."""
    import config
    original_get_data_dir = config.get_data_dir
    config.get_data_dir = lambda: tmp_path
    
    try:
        df = load_false_memory_data()
        results = run_anova(df)
        
        # Verify schema
        assert 'f_statistic' in results
        assert 'p_value' in results
        assert 'effect_size' in results
        assert 'degrees_of_freedom' in results
        
        # Verify types
        assert isinstance(results['f_statistic'], float)
        assert isinstance(results['p_value'], float)
        assert isinstance(results['effect_size'], float)
        assert isinstance(results['degrees_of_freedom'], dict)
        assert 'num' in results['degrees_of_freedom']
        assert 'den' in results['degrees_of_freedom']
        
        # Verify values are reasonable
        assert results['f_statistic'] > 0
        assert 0 <= results['p_value'] <= 1
        assert 0 <= results['effect_size'] <= 1
    finally:
        config.get_data_dir = original_get_data_dir

def test_save_results(mock_data_file, mock_power_gate, tmp_path):
    """Test that save_results writes valid JSON."""
    import config
    original_get_data_dir = config.get_data_dir
    config.get_data_dir = lambda: tmp_path
    
    try:
        df = load_false_memory_data()
        results = run_anova(df)
        
        output_path = tmp_path / "analysis" / "anova_results.json"
        save_results(results, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            saved_results = json.load(f)
        
        # Verify schema matches
        assert 'f_statistic' in saved_results
        assert 'p_value' in saved_results
        assert 'effect_size' in saved_results
        assert 'degrees_of_freedom' in saved_results
        assert 'limitations' in saved_results
        assert 'biological_context' in saved_results
    finally:
        config.get_data_dir = original_get_data_dir

def test_main(mock_data_file, mock_power_gate, tmp_path, caplog):
    """Test the main CLI entry point."""
    import config
    original_get_data_dir = config.get_data_dir
    config.get_data_dir = lambda: tmp_path
    
    try:
        # Run main
        sys.argv = ['anova.py']
        main()
        
        # Check output file exists
        output_path = tmp_path / "analysis" / "anova_results.json"
        assert output_path.exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            results = json.load(f)
        
        assert 'f_statistic' in results
        assert 'p_value' in results
    finally:
        config.get_data_dir = original_get_data_dir

def test_missing_power_gate(mock_data_file, tmp_path, caplog):
    """Test that missing power gate raises SystemExit."""
    import config
    original_get_data_dir = config.get_data_dir
    config.get_data_dir = lambda: tmp_path
    
    try:
        # Do NOT create power_gate_passed.txt
        df = load_false_memory_data()
        
        with pytest.raises(SystemExit) as excinfo:
            run_anova(df)
        
        assert "Power Gate Failed" in str(excinfo.value)
    finally:
        config.get_data_dir = original_get_data_dir
