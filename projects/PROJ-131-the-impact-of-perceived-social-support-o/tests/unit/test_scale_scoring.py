"""
Unit tests for scale scoring logic (T011).
Verifies that scoring algorithms in analysis.scales match config definitions.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import yaml

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from analysis.scales import load_scale_config, score_cesd, score_gad7, score_pcl5, apply_scale_scoring

def test_load_scale_config():
    """Test that scale config loads correctly and matches expected keys."""
    config = load_scale_config()
    assert isinstance(config, dict), "Config must be a dictionary"
    assert 'CES-D' in config, "Config must contain 'CES-D' key"
    assert 'GAD-7' in config, "Config must contain 'GAD-7' key"
    
    # Verify structure of CES-D config
    cesd_config = config['CES-D']
    assert 'variable' in cesd_config, "CES-D config must have 'variable' key"
    assert 'type' in cesd_config, "CES-D config must have 'type' key"
    assert cesd_config['variable'] == 'depression', "CES-D variable must be 'depression'"
    
    # Verify structure of GAD-7 config
    gad_config = config['GAD-7']
    assert gad_config['variable'] == 'anxiety', "GAD-7 variable must be 'anxiety'"

def test_score_cesd_basic():
    """Test CES-D scoring with mock data."""
    # Create mock data with CES-D items (assuming 4 items for simplicity based on typical short forms)
    # In real data, column names would match the config's expected items
    mock_data = pd.DataFrame({
        'cesd_1': [1.0, 2.0, 3.0, 4.0],
        'cesd_2': [2.0, 3.0, 1.0, 4.0],
        'cesd_3': [1.0, 1.0, 2.0, 3.0],
        'cesd_4': [3.0, 2.0, 4.0, 1.0]
    })
    
    # Call the scoring function
    result = score_cesd(mock_data)
    
    # Verify output
    assert isinstance(result, pd.DataFrame), "Result must be a DataFrame"
    assert 'depression' in result.columns, "Result must contain 'depression' column"
    assert len(result) == len(mock_data), "Result must have same number of rows as input"
    
    # Check that scores are reasonable (sum of 4 items, each 1-4, so range 4-16)
    scores = result['depression']
    assert scores.min() >= 4.0, "Minimum CES-D score should be at least 4"
    assert scores.max() <= 16.0, "Maximum CES-D score should be at most 16"

def test_score_gad7_basic():
    """Test GAD-7 scoring with mock data."""
    # Create mock data with GAD-7 items (7 items)
    mock_data = pd.DataFrame({
        'gad_1': [1.0, 2.0, 3.0, 4.0, 1.0, 2.0, 3.0],
        'gad_2': [2.0, 3.0, 1.0, 4.0, 2.0, 3.0, 1.0],
        'gad_3': [1.0, 1.0, 2.0, 3.0, 1.0, 1.0, 2.0],
        'gad_4': [3.0, 2.0, 4.0, 1.0, 3.0, 2.0, 4.0],
        'gad_5': [2.0, 1.0, 3.0, 2.0, 2.0, 1.0, 3.0],
        'gad_6': [1.0, 3.0, 2.0, 1.0, 1.0, 3.0, 2.0],
        'gad_7': [2.0, 2.0, 1.0, 3.0, 2.0, 2.0, 1.0]
    })
    
    # Call the scoring function
    result = score_gad7(mock_data)
    
    # Verify output
    assert isinstance(result, pd.DataFrame), "Result must be a DataFrame"
    assert 'anxiety' in result.columns, "Result must contain 'anxiety' column"
    assert len(result) == len(mock_data), "Result must have same number of rows as input"
    
    # Check that scores are reasonable (sum of 7 items, each 1-4, so range 7-28)
    scores = result['anxiety']
    assert scores.min() >= 7.0, "Minimum GAD-7 score should be at least 7"
    assert scores.max() <= 28.0, "Maximum GAD-7 score should be at most 28"

def test_score_pcl5_basic():
    """Test PCL-5 scoring with mock data."""
    # Create mock data with PCL-5 items (20 items)
    mock_data = pd.DataFrame({
        f'pcl_{i}': np.random.randint(1, 5, 5) for i in range(1, 21)
    })
    
    # Call the scoring function
    result = score_pcl5(mock_data)
    
    # Verify output
    assert isinstance(result, pd.DataFrame), "Result must be a DataFrame"
    assert 'ptsd' in result.columns, "Result must contain 'ptsd' column"
    assert len(result) == len(mock_data), "Result must have same number of rows as input"
    
    # Check that scores are reasonable (sum of 20 items, each 1-5, so range 20-100)
    scores = result['ptsd']
    assert scores.min() >= 20.0, "Minimum PCL-5 score should be at least 20"
    assert scores.max() <= 100.0, "Maximum PCL-5 score should be at most 100"

def test_apply_scale_scoring_integration():
    """Test the full scale scoring pipeline on mock data."""
    # Create comprehensive mock data with all scale items
    mock_data = pd.DataFrame({
        # CES-D items (4 items)
        'cesd_1': [1.0, 2.0, 3.0, 4.0],
        'cesd_2': [2.0, 3.0, 1.0, 4.0],
        'cesd_3': [1.0, 1.0, 2.0, 3.0],
        'cesd_4': [3.0, 2.0, 4.0, 1.0],
        # GAD-7 items (7 items)
        'gad_1': [1.0, 2.0, 3.0, 4.0],
        'gad_2': [2.0, 3.0, 1.0, 4.0],
        'gad_3': [1.0, 1.0, 2.0, 3.0],
        'gad_4': [3.0, 2.0, 4.0, 1.0],
        'gad_5': [2.0, 1.0, 3.0, 2.0],
        'gad_6': [1.0, 3.0, 2.0, 1.0],
        'gad_7': [2.0, 2.0, 1.0, 3.0],
        # PCL-5 items (20 items)
        **{f'pcl_{i}': np.random.randint(1, 5, 4) for i in range(1, 21)}
    })
    
    # Apply full scoring pipeline
    result = apply_scale_scoring(mock_data)
    
    # Verify all three scores are present
    assert 'depression' in result.columns, "Result must contain 'depression' column"
    assert 'anxiety' in result.columns, "Result must contain 'anxiety' column"
    assert 'ptsd' in result.columns, "Result must contain 'ptsd' column"
    
    # Verify all scores are numeric and within expected ranges
    assert result['depression'].min() >= 4.0
    assert result['depression'].max() <= 16.0
    
    assert result['anxiety'].min() >= 7.0
    assert result['anxiety'].max() <= 28.0
    
    assert result['ptsd'].min() >= 20.0
    assert result['ptsd'].max() <= 100.0

def test_scale_config_yaml_validity():
    """Test that the scale config file is valid YAML."""
    config_path = code_dir / "config" / "scales.yaml"
    assert config_path.exists(), f"Config file must exist at {config_path}"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    assert config is not None, "Config must not be empty"
    assert isinstance(config, dict), "Config must be a dictionary"
    assert 'CES-D' in config, "Config must contain 'CES-D'"
    assert 'GAD-7' in config, "Config must contain 'GAD-7'"