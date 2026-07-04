"""
Contract test for retrieval output schema.

Validates that the retrieval results produced by code/retrieval.py
conform to the expected schema defined in code/data_models.py.

This test ensures that:
1. The output CSV contains all required columns.
2. Data types match expectations (numeric for values, string for flags).
3. Censorship status is valid (UpperLimit, Detected, or None).
4. Water abundance values are within physically plausible bounds.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data_models import RetrievalResult, CensorshipStatus, PlanetCategory
from utils import CensoredDataError


def validate_retrieval_schema(df: pd.DataFrame) -> None:
    """
    Validates the schema of a retrieval results DataFrame.
    
    Args:
        df: DataFrame containing retrieval results.
        
    Raises:
        AssertionError: If the schema is invalid.
        ValueError: If data values are out of expected ranges.
    """
    required_columns = {
        'planet_name',
        'equilibrium_temp',
        'host_star_metallicity',
        'spectral_resolution',
        'snr',
        'log10_water_mixing_ratio',
        'water_mixing_ratio_std',
        'censorship_status',
        'planet_category'
    }
    
    # Check for required columns
    missing_cols = required_columns - set(df.columns)
    assert not missing_cols, f"Missing required columns: {missing_cols}"
    
    # Validate censorship_status values
    valid_statuses = {status.value for status in CensorshipStatus} | {None}
    invalid_statuses = set(df['censorship_status'].dropna().unique()) - valid_statuses
    assert not invalid_statuses, f"Invalid censorship statuses found: {invalid_statuses}"
    
    # Validate planet_category values
    valid_categories = {cat.value for cat in PlanetCategory} | {None}
    invalid_categories = set(df['planet_category'].dropna().unique()) - valid_categories
    assert not invalid_categories, f"Invalid planet categories found: {invalid_categories}"
    
    # Validate numeric columns
    numeric_cols = [
        'equilibrium_temp',
        'host_star_metallicity',
        'spectral_resolution',
        'snr',
        'log10_water_mixing_ratio',
        'water_mixing_ratio_std'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            non_numeric = df[col][~pd.to_numeric(df[col], errors='coerce').notna() & df[col].notna()]
            assert len(non_numeric) == 0, f"Column {col} contains non-numeric values"
            
            # Check for plausible ranges
            if col == 'equilibrium_temp':
                assert df[col].min() >= 0, "Equilibrium temperature cannot be negative"
                assert df[col].max() <= 5000, "Equilibrium temperature exceeds plausible range (>5000K)"
                
            if col == 'log10_water_mixing_ratio':
                # Water mixing ratio typically between 1e-10 and 1e-2
                assert df[col].min() >= -10, "Water mixing ratio too low (<1e-10)"
                assert df[col].max() <= 0, "Water mixing ratio too high (>1)"
                
            if col == 'water_mixing_ratio_std':
                assert df[col].min() >= 0, "Standard deviation cannot be negative"
                
            if col == 'spectral_resolution':
                assert df[col].min() >= 1, "Spectral resolution must be at least 1"
                
            if col == 'snr':
                assert df[col].min() >= 0, "SNR cannot be negative"


def test_retrieval_output_schema():
    """
    Contract test to verify retrieval output schema.
    
    This test loads the retrieval results CSV and validates its structure
    against the expected schema.
    """
    results_path = project_root / 'data' / 'processed' / 'retrieval_results.csv'
    
    if not results_path.exists():
        pytest.skip(f"Retrieval results file not found at {results_path}. "
                   "Run retrieval pipeline first.")
    
    # Load the retrieval results
    df = pd.read_csv(results_path)
    
    # Validate the schema
    validate_retrieval_schema(df)
    
    # Additional checks for data integrity
    assert len(df) > 0, "Retrieval results file is empty"
    
    # Check that we have a mix of detected and upper limit values
    if 'censorship_status' in df.columns:
        detected_count = len(df[df['censorship_status'] == CensorshipStatus.DETECTED.value])
        upper_limit_count = len(df[df['censorship_status'] == CensorshipStatus.UPPER_LIMIT.value])
        
        # Log counts for debugging (not assertion)
        print(f"Detected: {detected_count}, Upper Limits: {upper_limit_count}")
        
        # At least some results should exist (either detected or upper limits)
        assert detected_count + upper_limit_count > 0, "No valid retrieval results found"


def test_retrieval_result_dataclass_compliance():
    """
    Test that the DataFrame rows can be instantiated as RetrievalResult dataclasses.
    
    This ensures the data conforms to the data model definition.
    """
    results_path = project_root / 'data' / 'processed' / 'retrieval_results.csv'
    
    if not results_path.exists():
        pytest.skip(f"Retrieval results file not found at {results_path}. "
                   "Run retrieval pipeline first.")
    
    df = pd.read_csv(results_path)
    
    # Try to instantiate each row as a RetrievalResult
    for idx, row in df.iterrows():
        try:
            result = RetrievalResult(
                planet_name=row['planet_name'],
                equilibrium_temp=row['equilibrium_temp'],
                host_star_metallicity=row['host_star_metallicity'],
                spectral_resolution=row['spectral_resolution'],
                snr=row['snr'],
                log10_water_mixing_ratio=row['log10_water_mixing_ratio'],
                water_mixing_ratio_std=row['water_mixing_ratio_std'],
                censorship_status=CensorshipStatus(row['censorship_status']) if pd.notna(row['censorship_status']) else None,
                planet_category=PlanetCategory(row['planet_category']) if pd.notna(row['planet_category']) else None
            )
            
            # Verify the instantiated object has expected attributes
            assert hasattr(result, 'planet_name')
            assert hasattr(result, 'log10_water_mixing_ratio')
            assert hasattr(result, 'censorship_status')
            
        except (ValueError, TypeError) as e:
            pytest.fail(f"Row {idx} cannot be instantiated as RetrievalResult: {str(e)}")


if __name__ == '__main__':
    # Run tests when executed directly
    pytest.main([__file__, '-v'])