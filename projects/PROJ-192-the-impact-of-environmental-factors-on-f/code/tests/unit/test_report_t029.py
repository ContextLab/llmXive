import os
import tempfile
import pandas as pd
import pytest
import numpy as np
from pathlib import Path
from src.pipelines.report import determine_top_drivers_stability, determine_top_drivers_and_ranking_stability

@pytest.fixture
def sample_permanova_data():
    """Create a sample PERMANOVA dataframe with multiple biomes."""
    data = {
        'biome': ['Forest', 'Forest', 'Grassland', 'Grassland', 'Desert', 'Desert'],
        'term': ['pH', 'Moisture', 'pH', 'Moisture', 'pH', 'Moisture'],
        'R2': [0.3, 0.1, 0.1, 0.4, 0.2, 0.5],
        'p-value': [0.01, 0.05, 0.05, 0.01, 0.01, 0.01],
        'p-value_adj': [0.02, 0.06, 0.06, 0.02, 0.02, 0.02]
    }
    return pd.DataFrame(data)

def test_determine_top_drivers_stability_pass(sample_permanova_data):
    """
    Test case where top drivers are consistent (low std dev).
    In this data:
    Forest: pH (0.3) > Moisture (0.1) -> Top: pH
    Grassland: Moisture (0.4) > pH (0.1) -> Top: Moisture
    Desert: Moisture (0.5) > pH (0.2) -> Top: Moisture
    
    Global R2 sum: pH=0.6, Moisture=1.0.
    Global Rank: Moisture (0), pH (1).
    Top drivers ranks:
    Forest -> pH -> 1
    Grassland -> Moisture -> 0
    Desert -> Moisture -> 0
    
    Values: [1, 0, 0]. Mean = 0.33. Std Dev = sqrt(((0.66)^2 + (-0.33)^2 + (-0.33)^2)/2) approx 0.47.
    0.47 <= 0.5 -> Pass.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "input.csv")
        output_file = os.path.join(tmpdir, "output.csv")
        
        sample_permanova_data.to_csv(input_file, index=False)
        
        std_dev, passed = determine_top_drivers_stability(sample_permanova_data, output_file)
        
        assert passed is True
        assert std_dev <= 0.5
        
        # Verify output file
        assert os.path.exists(output_file)
        result_df = pd.read_csv(output_file)
        assert 'top_driver' in result_df.columns
        assert 'passed' in result_df.columns
        assert all(result_df['passed'])

def test_determine_top_drivers_stability_fail(sample_permanova_data):
    """
    Modify data to create high variance in ranks.
    We need a scenario where top drivers have very different global ranks.
    Add a third driver 'Temp' that is top in one biome but has low global rank.
    """
    data = {
        'biome': ['Forest', 'Forest', 'Grassland', 'Grassland', 'Desert', 'Desert', 'Tundra', 'Tundra'],
        'term': ['pH', 'Moisture', 'pH', 'Moisture', 'pH', 'Moisture', 'Temp', 'pH'],
        'R2': [0.3, 0.1, 0.1, 0.4, 0.2, 0.5, 0.6, 0.1], 
        'p-value': [0.01]*8,
        'p-value_adj': [0.02]*8
    }
    df = pd.DataFrame(data)
    
    # Global R2:
    # pH: 0.3+0.1+0.2+0.1 = 0.7
    # Moisture: 0.1+0.4+0.5 = 1.0
    # Temp: 0.6
    # Ranks: Moisture(0), Temp(1), pH(2)
    
    # Top Drivers:
    # Forest: pH (2)
    # Grassland: Moisture (0)
    # Desert: Moisture (0)
    # Tundra: Temp (1)
    
    # Values: [2, 0, 0, 1]. Mean = 0.75.
    # Std Dev calculation:
    # (2-0.75)^2 = 1.56
    # (0-0.75)^2 = 0.56
    # (0-0.75)^2 = 0.56
    # (1-0.75)^2 = 0.06
    # Sum = 2.74. Var = 2.74/3 = 0.91. Std = 0.95.
    # 0.95 > 0.5 -> Fail.
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "output.csv")
        std_dev, passed = determine_top_drivers_stability(df, output_file)
        
        assert passed is False
        assert std_dev > 0.5

def test_determine_top_drivers_empty():
    """Test behavior with empty dataframe."""
    df = pd.DataFrame(columns=['biome', 'term', 'R2', 'p-value', 'p-value_adj'])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "output.csv")
        std_dev, passed = determine_top_drivers_stability(df, output_file)
        
        assert passed is False
        assert os.path.exists(output_file)
        
        result_df = pd.read_csv(output_file)
        assert result_df.empty

def test_determine_top_drivers_and_ranking_stability_integration(sample_permanova_data):
    """Test the wrapper function that loads from file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "input.csv")
        output_file = os.path.join(tmpdir, "output.csv")
        
        sample_permanova_data.to_csv(input_file, index=False)
        
        std_dev, passed = determine_top_drivers_and_ranking_stability(input_file, output_file)
        
        assert passed is True
        assert os.path.exists(output_file)
