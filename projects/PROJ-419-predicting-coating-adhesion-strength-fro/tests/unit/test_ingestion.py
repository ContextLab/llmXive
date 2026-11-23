import pytest
import pandas as pd
import numpy as np
from ingestion import sample_dataset_to_memory_limit, filter_astm_d4541_records, resolve_duplicates

# Constants for testing
TEST_MAX_ROWS = 100

def test_sample_dataset_to_memory_limit_reduction():
    """Test that sampling reduces dataset when rows > limit."""
    # Create a large dummy dataset
    data = {'value': range(200), 'id': range(200)}
    df_large = pd.DataFrame(data)
    
    # Temporarily patch MAX_ROWS for this test
    import ingestion
    original_max = ingestion.MAX_ROWS
    ingestion.MAX_ROWS = TEST_MAX_ROWS
    
    try:
        result = sample_dataset_to_memory_limit(df_large)
        assert len(result) == TEST_MAX_ROWS, f"Expected {TEST_MAX_ROWS} rows, got {len(result)}"
        assert len(result) < len(df_large), "Result should be smaller than input"
    finally:
        ingestion.MAX_ROWS = original_max

def test_sample_dataset_to_memory_limit_no_change():
    """Test that sampling does not change dataset when rows <= limit."""
    # Create a small dummy dataset
    data = {'value': range(50), 'id': range(50)}
    df_small = pd.DataFrame(data)
    
    import ingestion
    original_max = ingestion.MAX_ROWS
    ingestion.MAX_ROWS = TEST_MAX_ROWS
    
    try:
        result = sample_dataset_to_memory_limit(df_small)
        assert len(result) == len(df_small), "Result should be same size as input"
        assert result.equals(df_small), "Data should be identical"
    finally:
        ingestion.MAX_ROWS = original_max

def test_sample_dataset_reproducibility():
    """Test that sampling uses a fixed seed for reproducibility."""
    data = {'value': range(200), 'id': range(200)}
    df_large = pd.DataFrame(data)
    
    import ingestion
    original_max = ingestion.MAX_ROWS
    ingestion.MAX_ROWS = TEST_MAX_ROWS
    
    try:
        result1 = sample_dataset_to_memory_limit(df_large)
        result2 = sample_dataset_to_memory_limit(df_large)
        assert result1.equals(result2), "Sampling should be reproducible with fixed seed"
    finally:
        ingestion.MAX_ROWS = original_max
