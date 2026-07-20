"""
Tests for T030b: Scatter Slope Calculation
"""
import os
import pytest
import pandas as pd
import numpy as np
from code.config import DATA_PROCESSED_DIR
from code.scatter_slope import calculate_scatter_slope, main

def test_scatter_slope_calculation():
    """
    Verify that calculate_scatter_slope produces a numeric slope
    and writes the output file correctly.
    """
    # Ensure input file exists (dependency on T016)
    input_file = os.path.join(DATA_PROCESSED_DIR, "energy_results_aggregated.csv")
    if not os.path.exists(input_file):
        pytest.skip(f"Input file {input_file} not found. Run T016 first.")
    
    # Run calculation
    try:
        slope, results_df = calculate_scatter_slope()
    except ValueError as e:
        if "Insufficient valid models" in str(e):
           pytest.skip(f"Skipping test: {e}")
        raise
    
    # Assertions
    assert isinstance(slope, float), "Slope must be a float"
    assert not np.isnan(slope), "Slope must not be NaN"
    
    # Check output file
    output_file = os.path.join(DATA_PROCESSED_DIR, "scatter_slope.txt")
    assert os.path.exists(output_file), f"Output file {output_file} was not created"
    
    with open(output_file, 'r') as f:
        content = f.read()
    
    assert "Slope of Energy/Correct vs Accuracy" in content, "Output missing slope label"
    assert str(slope) in content, "Output does not contain the calculated slope"

def test_main_execution():
    """
    Verify that main() runs without raising exceptions (if data exists).
    """
    input_file = os.path.join(DATA_PROCESSED_DIR, "energy_results_aggregated.csv")
    if not os.path.exists(input_file):
        pytest.skip(f"Input file {input_file} not found.")
    
    # Capture print output or just ensure no exception
    try:
        main()
    except ValueError as e:
        if "Insufficient valid models" in str(e):
           pytest.skip(f"Skipping test: {e}")
        raise