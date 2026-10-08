import pytest
import pandas as pd
import os
from pathlib import Path
import tempfile
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.saving import save_permutation_results, save_sensitivity_summary
from config import get_config

def test_sensitivity_csv_schema():
    """
    Unit test for T030/T031: Verify the sensitivity DataFrame includes
    `correlation` and `empirical_p_value` for each window length.
    """
    # Create temporary directory for test output
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = os.path.join(tmp_dir, "sensitivity_summary.csv")
        
        # Mock sensitivity data
        sensitivity_data = {
            "window_lengths": [20, 30, 40],
            "correlations": [0.45, 0.52, 0.48],
            "p_values": [0.02, 0.01, 0.03]
        }

        # Call the function
        save_sensitivity_summary(sensitivity_data, output_path)

        # Verify file exists
        assert os.path.exists(output_path), "sensitivity_summary.csv was not created"

        # Load and check schema
        df = pd.read_csv(output_path)
        
        # Assert required columns exist
        assert "window_length" in df.columns, "Missing 'window_length' column"
        assert "correlation" in df.columns, "Missing 'correlation' column"
        assert "empirical_p_value" in df.columns, "Missing 'empirical_p_value' column"

        # Assert 'empirical_p_value' is non-null
        assert df["empirical_p_value"].notnull().all(), "empirical_p_value contains null values"
        
        # Assert data types and values match input
        assert df["window_length"].tolist() == [20, 30, 40]
        assert df["correlation"].tolist() == [0.45, 0.52, 0.48]
        assert df["empirical_p_value"].tolist() == [0.02, 0.01, 0.03]

def test_permutation_csv_schema():
    """
    Unit test for T030: Verify permutation_results.csv schema.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = os.path.join(tmp_dir, "permutation_results.csv")
        
        # Mock permutation data
        p_values = [0.05, 0.12, 0.08, 0.01, 0.99]
        
        # Call the function
        save_permutation_results(p_values, [], output_path)

        # Verify file exists
        assert os.path.exists(output_path), "permutation_results.csv was not created"

        # Load and check schema
        df = pd.read_csv(output_path)
        
        # Assert required columns exist
        assert "shuffle_id" in df.columns, "Missing 'shuffle_id' column"
        assert "correlation" in df.columns, "Missing 'correlation' column"
        
        # Assert data integrity
        assert len(df) == len(p_values)
        assert df["correlation"].tolist() == p_values
        assert df["shuffle_id"].tolist() == list(range(len(p_values)))