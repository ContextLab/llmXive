"""
Integration test for the high variance flagging logic (T015).

This test verifies that:
1. Entries with high coefficient of variation (CV > 0.5) are correctly identified.
2. Low variance entries are preserved.
3. The report is generated correctly.
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add the project root to the path to allow imports
# Assuming this test runs from the project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingestion.flag_high_variance import (
    flag_high_variance_entries, 
    calculate_coefficient_of_variation,
    save_results,
    HIGH_VARIANCE_THRESHOLD
)


def test_calculate_cv():
    """Test the CV calculation function."""
    # Low variance
    series_low = pd.Series([10, 10.1, 9.9, 10.0])
    cv_low = calculate_coefficient_of_variation(series_low)
    assert cv_low < 0.5, f"Low variance series should have CV < 0.5, got {cv_low}"

    # High variance
    series_high = pd.Series([10, 20, 5, 30]) # Mean ~ 16.25, Std ~ 9.5 -> CV ~ 0.58
    cv_high = calculate_coefficient_of_variation(series_high)
    assert cv_high > 0.5, f"High variance series should have CV > 0.5, got {cv_high}"

    # Edge cases
    assert calculate_coefficient_of_variation(pd.Series([5])) == 0.0
    assert calculate_coefficient_of_variation(pd.Series([0, 0, 0])) == 0.0 # Mean is 0


def test_flag_high_variance_logic():
    """Test the main flagging logic with a synthetic dataset."""
    
    # Create a dataframe with known high and low variance groups
    data = {
        'polymer_class': ['Polyimide', 'Polyimide', 'Polyimide', 'Cellulose', 'Cellulose', 'Cellulose'],
        'smiles': ['C1=CC=C(C=C1)N(=O)O', 'C1=CC=C(C=C1)N(=O)O', 'C1=CC=C(C=C1)N(=O)O', 'C(C1=CC=CC=C1)O', 'C(C1=CC=CC=C1)O', 'C(C1=CC=CC=C1)O'],
        'permeability_o2': [10.0, 10.2, 10.1, 50.0, 150.0, 200.0], # Polyimide: Low CV; Cellulose: High CV
        'selectivity_o2_n2': [4.0, 4.1, 3.9, 2.0, 2.1, 1.9] # Cellulose: Low CV on this metric, but high on permeability
    }
    
    df = pd.DataFrame(data)
    
    # Group by polymer_class and smiles
    # Metric: permeability_o2
    cleaned_df, flagged_df, report = flag_high_variance_entries(
        df, 
        group_by_cols=['polymer_class', 'smiles'], 
        metric_cols=['permeability_o2']
    )
    
    # Verify counts
    # Polyimide group (3 rows) should be kept (Low CV)
    # Cellulose group (3 rows) should be excluded (High CV in permeability)
    assert len(cleaned_df) == 3, f"Expected 3 rows kept (Polyimide), got {len(cleaned_df)}"
    assert len(flagged_df) == 3, f"Expected 3 rows flagged (Cellulose), got {len(flagged_df)}"
    
    # Verify content
    assert all(cleaned_df['polymer_class'] == 'Polyimide')
    assert all(flagged_df['polymer_class'] == 'Cellulose')
    
    # Verify report
    assert report['excluded_count'] == 3
    assert report['kept_count'] == 3
    assert report['threshold'] == HIGH_VARIANCE_THRESHOLD


def test_flag_high_variance_save_results():
    """Test that results are saved correctly to disk."""
    df = pd.DataFrame({
        'polymer_class': ['A', 'A', 'A'],
        'smiles': ['S1', 'S1', 'S1'],
        'metric': [10, 50, 90] # High variance
    })
    
    cleaned, flagged, report = flag_high_variance_entries(
        df, 
        group_by_cols=['polymer_class', 'smiles'], 
        metric_cols=['metric']
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir)
        save_results(flagged, report, output_dir=output_path)
        
        # Check files exist
        assert (output_path / "excluded_high_variance_entries.json").exists()
        assert (output_path / "high_variance_report.json").exists()
        
        # Check report content
        with open(output_path / "high_variance_report.json") as f:
            loaded_report = json.load(f)
        
        assert loaded_report['excluded_count'] == 3
