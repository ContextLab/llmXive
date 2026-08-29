"""
Integration tests for data ingestion pipeline.
Verifies that the pipeline produces a valid CSV with >= 500 rows.
"""
import os
import sys
import pytest
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion import run_ingestion, validate_data_quality, validate_critical_cooling_rate

OUTPUT_PATH = "data/processed/processed_alloys.csv"

@pytest.mark.integration
def test_ingestion_pipeline_produces_valid_csv():
    """
    Test that run_ingestion produces a CSV file with:
    - At least 500 rows
    - Required columns present
    - No NaN in critical columns
    """
    # Run the pipeline
    # Note: This test might be slow if it downloads data, but it's necessary for integration.
    # We assume the data is available or the test is skipped if network is down.
    
    try:
        df = run_ingestion()
    except Exception as e:
        pytest.fail(f"Ingestion pipeline failed: {str(e)}")
    
    # Check file exists
    assert os.path.exists(OUTPUT_PATH), f"Output file {OUTPUT_PATH} does not exist."
    
    # Load and check
    df_loaded = pd.read_csv(OUTPUT_PATH)
    
    # Check row count
    assert len(df_loaded) >= 500, f"Expected >= 500 rows, got {len(df_loaded)}"
    
    # Check columns
    required_cols = ['composition', 'critical_cooling_rate', 'mixing_enthalpy', 
                     'atomic_size_mismatch', 'electronegativity_variance']
    for col in required_cols:
        assert col in df_loaded.columns, f"Missing column: {col}"
    
    # Check NaN in critical columns
    assert df_loaded['critical_cooling_rate'].isna().sum() == 0, "NaN found in critical_cooling_rate"
    assert df_loaded['mixing_enthalpy'].isna().sum() == 0, "NaN found in mixing_enthalpy"
    
    # Check variance
    assert df_loaded['critical_cooling_rate'].var() > 0, "Zero variance in critical_cooling_rate"

@pytest.mark.integration
def test_filter_ternary_alloys_logic():
    """
    Test that the filtering logic correctly identifies ternary alloys.
    """
    # Create a mock dataframe
    data = {
        'composition': ['Fe50Cr30Ni20', 'Fe50Cr30', 'Fe50Cr30Ni10Cu10', 'Unknown'],
        'critical_cooling_rate': [10.0, 20.0, 30.0, 40.0],
        'source_label': ['known', 'known', 'known', 'unknown']
    }
    df = pd.DataFrame(data)
    
    from ingestion import filter_ternary_alloys
    filtered = filter_ternary_alloys(df)
    
    # Only Fe50Cr30Ni20 (3 elements) and Fe50Cr30Ni10Cu10 (4 elements -> filtered out)
    # Wait, Fe50Cr30Ni10Cu10 has 4 elements.
    # Fe50Cr30 has 2 elements.
    # So only Fe50Cr30Ni20 should remain?
    # Let's check the regex logic in parse_composition.
    # Fe50Cr30Ni20 -> 3 elements.
    # Fe50Cr30 -> 2 elements.
    # Fe50Cr30Ni10Cu10 -> 4 elements.
    # Unknown -> 0 elements.
    # So result should have 1 row.
    assert len(filtered) == 1, f"Expected 1 ternary alloy, got {len(filtered)}"
    assert filtered.iloc[0]['composition'] == 'Fe50Cr30Ni20'
