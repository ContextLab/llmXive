"""
Unit tests for the synthetic data generator (T007).
"""
import os
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_synthetic import main, calculate_time_to_peak, SEED

def test_seed_determinism():
    """Test that the generator produces deterministic output with seed=42."""
    # Run the generator twice
    main()
    path1 = Path("data/raw/synthetic_baseline.csv")
    df1 = pd.read_csv(path1)
    
    # Delete and regenerate
    path1.unlink()
    main()
    df2 = pd.read_csv(path1)
    
    # Compare
    pd.testing.assert_frame_equal(df1, df2)
    
def test_output_file_exists():
    """Test that the output file is created."""
    main()
    output_path = Path("data/raw/synthetic_baseline.csv")
    assert output_path.exists(), "Output file should exist"
    
def test_output_columns():
    """Test that the output has the required columns."""
    main()
    df = pd.read_csv("data/raw/synthetic_baseline.csv")
    expected_cols = [
        'sample_id', 'cold_work', 'annealing_temp', 
        'Mn_content', 'Mg_content', 'Si_content', 'Cu_content',
        'time_to_peak_softening'
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing column: {col}"
        
def test_physical_bounds():
    """Test that generated data respects physical bounds."""
    main()
    df = pd.read_csv("data/raw/synthetic_baseline.csv")
    
    # Cold work should be between 0 and 100
    assert df['cold_work'].min() >= 0, "Cold work should be >= 0"
    assert df['cold_work'].max() <= 100, "Cold work should be <= 100"
    
    # Time to peak should be positive
    assert df['time_to_peak_softening'].min() > 0, "Time to peak should be positive"
    
    # Composition values should be non-negative
    for col in ['Mn_content', 'Mg_content', 'Si_content', 'Cu_content']:
        assert df[col].min() >= 0, f"{col} should be non-negative"
        
def test_model_physics():
    """Test that the physical model produces expected trends."""
    # Higher cold work should lead to lower time-to-peak
    # Higher temperature should lead to lower time-to-peak
    # Higher alloy content should lead to higher time-to-peak
    
    # Test cold work effect
    cw_low = 10.0
    cw_high = 90.0
    temp = 300.0
    mn, mg, si, cu = 0.5, 0.5, 0.5, 0.5
    
    t_low = calculate_time_to_peak(cw_low, temp, mn, mg, si, cu)
    t_high = calculate_time_to_peak(cw_high, temp, mn, mg, si, cu)
    
    assert t_high < t_low, "Higher cold work should reduce time-to-peak"
    
    # Test temperature effect
    temp_low = 200.0
    temp_high = 400.0
    
    t_low_temp = calculate_time_to_peak(50.0, temp_low, mn, mg, si, cu)
    t_high_temp = calculate_time_to_peak(50.0, temp_high, mn, mg, si, cu)
    
    assert t_high_temp < t_low_temp, "Higher temperature should reduce time-to-peak"
    
    # Test alloy effect
    alloy_low = 0.0
    alloy_high = 1.0
    
    t_no_alloy = calculate_time_to_peak(50.0, 300.0, alloy_low, alloy_low, alloy_low, alloy_low)
    t_high_alloy = calculate_time_to_peak(50.0, 300.0, alloy_high, alloy_high, alloy_high, alloy_high)
    
    assert t_high_alloy > t_no_alloy, "Higher alloy content should increase time-to-peak"
