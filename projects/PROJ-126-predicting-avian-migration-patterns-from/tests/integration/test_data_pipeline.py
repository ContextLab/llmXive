import pytest
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocessing import run_first_arrival_sweep, load_aggregated_data
from config import DATA_PROCESSED

def test_end_to_end_first_arrival_sweep():
    """
    Integration test: Run the full first arrival sweep pipeline.
    Verifies that the output file is created and contains valid data.
    """
    # Ensure input data exists (simulated by grid_aggregated.csv)
    input_file = DATA_PROCESSED / "grid_aggregated.csv"
    assert input_file.exists(), "Input file grid_aggregated.csv missing for integration test."

    # Run the pipeline
    output_path = run_first_arrival_sweep()
    
    # Verify output file exists
    assert Path(output_path).exists(), f"Output file {output_path} not created."

    # Verify output content
    df = pd.read_csv(output_path)
    
    # Check columns
    expected_cols = ['grid_id', 'week', 'arrival_date_3', 'arrival_date_5', 'arrival_date_10', 'status']
    assert list(df.columns) == expected_cols, f"Columns mismatch: {list(df.columns)}"

    # Check that 'A' (count 14) is present and determined
    row_a = df[df['grid_id'] == 'A']
    assert len(row_a) == 1, "Grid cell A missing from output."
    assert row_a['status'].iloc[0] == 'determined', "Grid cell A should be determined."
    
    # Check that 'B' (count 5) is NOT present
    row_b = df[df['grid_id'] == 'B']
    assert len(row_b) == 0, "Grid cell B should be filtered out."

    # Check that 'C' (count 10) is present and determined
    row_c = df[df['grid_id'] == 'C']
    assert len(row_c) == 1, "Grid cell C missing from output."
    assert row_c['status'].iloc[0] == 'determined', "Grid cell C should be determined."

    # Check that 'D' (count 20) is present and determined
    row_d = df[df['grid_id'] == 'D']
    assert len(row_d) == 1, "Grid cell D missing from output."
    assert row_d['status'].iloc[0] == 'determined', "Grid cell D should be determined."

def test_output_file_schema():
    """Verify the output file schema matches the specification."""
    output_file = DATA_PROCESSED / "first_arrival_sweep.csv"
    if not output_file.exists():
        # Run the pipeline first
        run_first_arrival_sweep()
    
    df = pd.read_csv(output_file)
    
    # Check required columns
    required_cols = {'grid_id', 'week', 'arrival_date_3', 'arrival_date_5', 'arrival_date_10', 'status'}
    assert required_cols.issubset(set(df.columns)), "Missing required columns."
    
    # Check date columns are not all null for determined cells
    determined = df[df['status'] == 'determined']
    if not determined.empty:
        for col in ['arrival_date_3', 'arrival_date_5', 'arrival_date_10']:
            assert not determined[col].isna().all(), f"Column {col} should not be all null for determined cells."
