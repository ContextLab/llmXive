import pytest
import pandas as pd
import numpy as np
from ingestion import calculate_cronbach_alpha, generate_procrastination_data

def test_cronbach_alpha_valid():
    """
    Test Cronbach's alpha calculation with known data.
    """
    # Create a DataFrame with perfect correlation (alpha should be 1)
    data = {
        'item_1': [1, 2, 3, 4, 5],
        'item_2': [1, 2, 3, 4, 5],
        'item_3': [1, 2, 3, 4, 5]
    }
    df = pd.DataFrame(data)
    alpha = calculate_cronbach_alpha(df, ['item_1', 'item_2', 'item_3'])
    assert np.isclose(alpha, 1.0, atol=0.01)

def test_cronbach_alpha_low():
    """
    Test Cronbach's alpha with uncorrelated data.
    """
    np.random.seed(42)
    data = {
        'item_1': np.random.rand(100),
        'item_2': np.random.rand(100),
        'item_3': np.random.rand(100)
    }
    df = pd.DataFrame(data)
    alpha = calculate_cronbach_alpha(df, ['item_1', 'item_2', 'item_3'])
    # Alpha should be low, likely < 0.5 for random data
    assert alpha < 0.5

def test_generate_procrastination_data_schema():
    """
    Test that generated procrastination data has correct schema.
    """
    df = generate_procrastination_data(10, 42)
    expected_cols = ['participant_id'] + [f'procrastination_item_{i}' for i in range(1, 11)]
    assert list(df.columns) == expected_cols
    assert len(df) == 10
