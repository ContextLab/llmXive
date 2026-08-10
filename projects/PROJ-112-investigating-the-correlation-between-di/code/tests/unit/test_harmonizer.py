import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from src.ingestion.harmonizer import (
    load_agp_data,
    load_ukbb_data,
    filter_samples,
    harmonize_and_merge,
    MIN_READS,
    MIN_FIBER,
    MAX_FIBER
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def sample_agp_df():
    data = {
        "sample_id": ["A1", "A2", "A3", "A4"],
        "fiber_g_day": [10.0, 250.0, np.nan, 5.0], # 250 is > 200, nan is missing
        "total_reads": [10000, 4000, 6000, 1000]   # 4000 < 5000, 1000 < 5000
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_ukbb_df():
    data = {
        "sample_id": ["U1", "U2", "U3", "U4"],
        "fiber_intake_g": [15.0, 0.0, 50.0, -5.0], # 0 is ok, -5 is < 0
        "total_reads": [20000, 5000, 3000, 8000]   # 3000 < 5000
    }
    return pd.DataFrame(data)

def test_filter_samples_agp(sample_agp_df, temp_dir):
    # Save to temp file to simulate real usage if needed, but function takes DF
    # We pass the DF directly to filter_samples logic (extracted or adapted)
    # The function signature in harmonizer is: filter_samples(df, fiber_col, cohort_name)
    
    filtered_df, removed_count, reasons = filter_samples(
        sample_agp_df.copy(), 
        "fiber_g_day", 
        "AGP"
    )

    # Expected removals:
    # A2: fiber > 200 (250)
    # A3: missing fiber
    # A4: reads < 5000 (1000)
    # A1: reads >= 5000 (10000), fiber ok (10) -> KEPT
    
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]["sample_id"] == "A1"
    assert removed_count == 3
    assert reasons["missing_fiber"] == 1
    assert reasons["low_reads"] == 2 # A3 has nan fiber so dropped first, then A4 dropped for reads? 
    # Wait, logic order:
    # 1. Drop nan fiber: A3 dropped. (reason: missing_fiber=1). Remaining: A1, A2, A4.
    # 2. Drop low reads: A4 (1000) dropped. (reason: low_reads=1). Remaining: A1, A2.
    # 3. Drop out of range: A2 (250) dropped. (reason: out_of_range_fiber=1). Remaining: A1.
    # Total removed: 3.
    
    assert reasons["low_reads"] == 1
    assert reasons["out_of_range_fiber"] == 1

def test_filter_samples_ukbb(sample_ukbb_df):
    filtered_df, removed_count, reasons = filter_samples(
        sample_ukbb_df.copy(),
        "fiber_intake_g",
        "UKBB"
    )
    
    # Expected:
    # U1: 15g, 20k reads -> KEEP
    # U2: 0g, 5k reads -> KEEP (0 is >= 0)
    # U3: 50g, 3k reads -> DROP (reads < 5000)
    # U4: -5g -> DROP (fiber < 0)
    
    assert len(filtered_df) == 2
    assert set(filtered_df["sample_id"].tolist()) == {"U1", "U2"}
    assert removed_count == 2
    assert reasons["low_reads"] == 1
    assert reasons["out_of_range_fiber"] == 1

def test_harmonize_and_merge_integration(sample_agp_df, sample_ukbb_df, temp_dir):
    agp_path = temp_dir / "agp.tsv"
    ukbb_path = temp_dir / "ukbb.tsv"
    out_path = temp_dir / "merged.tsv"

    sample_agp_df.to_csv(agp_path, sep='\t', index=False)
    sample_ukbb_df.to_csv(ukbb_path, sep='\t', index=False)

    result_df = harmonize_and_merge(agp_path, ukbb_path, out_path)

    assert out_path.exists()
    assert len(result_df) == 3 # A1 (kept), U1 (kept), U2 (kept)
    assert "cohort" in result_df.columns
    assert "fiber_g_day" in result_df.columns
    
    # Check cohorts
    assert result_df[result_df["sample_id"] == "A1"]["cohort"].iloc[0] == "AGP"
    assert result_df[result_df["sample_id"] == "U1"]["cohort"].iloc[0] == "UKBB"
