import pandas as pd
from pathlib import Path
from config import get_project_root

def test_thin_pipeline_outputs():
    root = get_project_root()
    
    # Check if files exist
    cohort_file = root / "data" / "processed" / "ingested_cohort.parquet"
    pairs_file = root / "data" / "processed" / "user_track_pairs.parquet"
    summary_file = root / "data" / "final" / "regression_summary.csv"
    
    assert cohort_file.exists(), "ingested_cohort.parquet missing"
    assert pairs_file.exists(), "user_track_pairs.parquet missing"
    assert summary_file.exists(), "regression_summary.csv missing"
    
    # Validate regression summary columns
    df = pd.read_csv(summary_file)
    required_cols = {'term', 'estimate', 'std_error', 't_value', 'p_value', 'vif'}
    assert required_cols.issubset(set(df.columns)), f"Missing columns in summary. Found: {df.columns}"
    assert not df.empty, "regression_summary.csv is empty"