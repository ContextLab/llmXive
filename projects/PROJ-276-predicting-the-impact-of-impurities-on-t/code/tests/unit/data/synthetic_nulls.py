import pandas as pd
import numpy as np

def create_test_nulls_df():
    """
    Create a test dataframe with >50% missing impurity data.
    Used for testing the exit code condition in download_supercon.py.
    """
    # Create 10 rows, 6 with missing impurity data (60% > 50%)
    data = {
        'Tc': [39.0, 40.0, 38.5, 39.2, 38.8, 39.5, 39.1, 39.3, 38.9, 39.4],
        'impurity_C': [0.01, np.nan, np.nan, 0.02, np.nan, np.nan, np.nan, 0.015, np.nan, np.nan],
        'impurity_O': [0.0, np.nan, np.nan, 0.01, np.nan, np.nan, np.nan, 0.005, np.nan, np.nan],
        'temp_K': [20.0, 25.0, 30.0, 22.0, 28.0, 24.0, 26.0, 23.0, 27.0, 21.0],
        'pressure_GPa': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'source': ['synthetic'] * 10
    }
    return pd.DataFrame(data)

# Also provide a valid dataset for positive tests
def create_valid_test_df():
    """Create a test dataframe with valid impurity data."""
    data = {
        'Tc': [39.0, 40.0, 38.5, 39.2, 38.8],
        'impurity_C': [0.01, 0.02, 0.015, 0.025, 0.018],
        'impurity_O': [0.0, 0.01, 0.005, 0.012, 0.008],
        'temp_K': [20.0, 25.0, 30.0, 22.0, 28.0],
        'pressure_GPa': [0.0, 0.0, 0.0, 0.0, 0.0],
        'source': ['synthetic'] * 5
    }
    return pd.DataFrame(data)