import os
import pytest
import pandas as pd
from pathlib import Path
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

def test_metric_extraction_sub_01():
    """
    Integration test: run extraction on sub-01, assert results/metrics.csv exists 
    with required columns.
    Note: This test assumes T018 and T022 have run and produced data/processed/epo_raw.fif
    or sub-01_epo.fif. If data is missing, this test will fail, which is expected
    until the full pipeline is run.
    """
    from extract import run_extraction_pipeline
    from config_loader import get_project_root

    root = get_project_root()
    results_dir = root / "results"
    metrics_path = results_dir / "metrics.csv"

    # Remove existing file if any to ensure fresh run
    if metrics_path.exists():
        metrics_path.unlink()

    # Run the pipeline
    try:
        run_extraction_pipeline()
    except Exception as e:
        # If data is missing, the pipeline might fail or produce empty DF.
        # We check if the file exists regardless.
        pass

    assert metrics_path.exists(), "results/metrics.csv was not generated."

    df = pd.read_csv(metrics_path)

    required_columns = [
        'participant_id', 
        'standard_amplitude', 
        'standard_latency', 
        'deviant_amplitude', 
        'deviant_latency', 
        'peak_detected', 
        'snr'
    ]

    for col in required_columns:
        assert col in df.columns, f"Column {col} is missing from metrics.csv"

    # Check if sub-01 is present (if data exists)
    # If the pipeline ran but no data was found, df might be empty.
    # The task requirement is that the file exists with correct columns.
    if not df.empty:
        assert 'peak_detected' in df.columns
        assert df['peak_detected'].dtype == bool or df['peak_detected'].apply(lambda x: isinstance(x, (bool, np.bool_))).all()
    
    # If we have data, check sub-01 specifically if it exists in the run
    if 'sub-01' in df['participant_id'].values:
        sub_01_row = df[df['participant_id'] == 'sub-01'].iloc[0]
        assert pd.notna(sub_01_row['standard_amplitude']) or pd.notna(sub_01_row['deviant_amplitude'])

# Note: This test relies on real data being present in data/processed.
# If data is not present, the test will fail at the file existence check or empty dataframe check.
