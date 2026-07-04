"""
Integration test for T014: Participant ID Merge Logic.

Verifies that the merge logic correctly identifies overlaps,
logs statistics, and enforces the minimum sample count constraint.
"""
import pytest
import pandas as pd
import sys
from pathlib import Path
import tempfile
import os

# Add code directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from code.utils.data_fetchers import fetch_and_cache # Mocking logic if needed
# We will test the logic by mocking the data fetches or creating temp files
# Since T014 logic is in 01_data_ingestion.py, we need to import the functions
# However, 01_data_ingestion.py has side effects (logging, sys.exit).
# We will test the core logic by importing the functions directly if possible,
# or by testing the file content execution in a controlled way.

# For this task, we assume the functions `fetch_agp_data`, `fetch_hrs_data`, `merge_datasets`
# are importable. If they are wrapped in `if __name__ == "__main__"`, we might need to
# refactor slightly or test via subprocess. 
# Given the constraints, we will test the `merge_datasets` logic directly by creating
# mock DataFrames, as the file I/O logic is straightforward.

def test_merge_logic_overlap_count():
    """Test that merge logic correctly counts overlaps and rejects low counts."""
    from code import data_ingestion # Import the module to access functions
    
    # Create mock data
    agp_data = pd.DataFrame({
        'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5'],
        'taxa_A': [10, 20, 30, 40, 50]
    })
    
    hrs_data = pd.DataFrame({
        'participant_id': ['P3', 'P4', 'P5', 'P6', 'P7'],
        'score': [100, 105, 110, 115, 120]
    })
    
    # Expected overlap: P3, P4, P5 -> count = 3
    
    # Temporarily patch the MIN_OVERLAP_SAMPLES to 2 to allow success in this test
    # or test the failure case with 1
    
    # Test Success Case (if min was 2)
    original_min = data_ingestion.MIN_OVERLAP_SAMPLES
    data_ingestion.MIN_OVERLAP_SAMPLES = 2
    
    merged_df, count = data_ingestion.merge_datasets(agp_data, hrs_data)
    
    assert count == 3, f"Expected overlap count 3, got {count}"
    assert len(merged_df) == 3
    assert list(merged_df['participant_id']) == ['P3', 'P4', 'P5']
    
    # Restore
    data_ingestion.MIN_OVERLAP_SAMPLES = original_min

def test_merge_logic_below_threshold():
    """Test that merge logic raises ValueError if overlap is too low."""
    from code import data_ingestion
    
    agp_data = pd.DataFrame({
        'participant_id': ['P1', 'P2'],
        'taxa_A': [10, 20]
    })
    
    hrs_data = pd.DataFrame({
        'participant_id': ['P3', 'P4'],
        'score': [100, 105]
    })
    
    # Expected overlap: 0
    
    # Set threshold high to force failure
    original_min = data_ingestion.MIN_OVERLAP_SAMPLES
    data_ingestion.MIN_OVERLAP_SAMPLES = 1
    
    with pytest.raises(ValueError) as exc_info:
        data_ingestion.merge_datasets(agp_data, hrs_data)
    
    assert "below the required minimum" in str(exc_info.value)
    
    # Restore
    data_ingestion.MIN_OVERLAP_SAMPLES = original_min

def test_merge_logic_column_normalization():
    """Test that different ID column names are normalized to 'participant_id'."""
    from code import data_ingestion
    
    # AGP with 'sample_id'
    agp_data = pd.DataFrame({
        'sample_id': ['A1', 'A2'],
        'val': [1, 2]
    })
    
    # HRS with 'person_id'
    hrs_data = pd.DataFrame({
        'person_id': ['A1', 'A2'],
        'score': [10, 20]
    })
    
    original_min = data_ingestion.MIN_OVERLAP_SAMPLES
    data_ingestion.MIN_OVERLAP_SAMPLES = 1
    
    merged_df, count = data_ingestion.merge_datasets(agp_data, hrs_data)
    
    assert 'participant_id' in merged_df.columns
    assert count == 2
    
    data_ingestion.MIN_OVERLAP_SAMPLES = original_min

if __name__ == "__main__":
    pytest.main([__file__, "-v"])