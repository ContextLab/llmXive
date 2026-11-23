import os
import pytest
import pandas as pd
import tempfile
from pathlib import Path
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ingestion.generate_outputs import count_valid_observations, generate_exclusion_summary

@pytest.fixture
def sample_df():
    data = {
        'species_name': ['A', 'A', 'A', 'B', 'B', 'C', 'C', 'C', 'C', 'C', 'C', 'C', 'C', 'C', 'C'],
        'N': [10, 20, 30, 10, 20, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        'P': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        'K': [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500],
        'pH': [5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5],
        'root_depth': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150]
    }
    return pd.DataFrame(data)

def test_count_valid_observations(sample_df):
    counts = count_valid_observations(sample_df)
    assert len(counts) == 3
    # Species A: 3, B: 2, C: 10
    assert counts[counts['species_name'] == 'A']['observation_count'].values[0] == 3
    assert counts[counts['species_name'] == 'B']['observation_count'].values[0] == 2
    assert counts[counts['species_name'] == 'C']['observation_count'].values[0] == 10

def test_generate_exclusion_summary(sample_df):
    counts = count_valid_observations(sample_df)
    excluded, logs = generate_exclusion_summary(counts, threshold=10)
    
    # Species A (3) and B (2) should be excluded. C (10) kept.
    assert len(excluded) == 2
    assert set(excluded['species_name']) == {'A', 'B'}
    assert 'observation_count < 10' in excluded['reason'].values
    
    assert len(logs) == 2
    assert logs[0]['reason'] == 'observation_count < 10'
    assert logs[1]['reason'] == 'observation_count < 10'