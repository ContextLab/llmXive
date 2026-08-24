"""
Unit tests for the screening module, specifically focusing on geometric feasibility filtering.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models.predict import filter_geometric_feasibility, calculate_tolerance_factor_from_ions
from utils.config import get_config_summary

# Constants for tolerance factor calculation (Goldschmidt)
# t = (r_A + r_X) / (sqrt(2) * (r_B + r_X))
# Stable range typically 0.8 <= t <= 1.1

class TestGeometricFeasibilityFilter:
    """Tests for the geometric feasibility filter (T025)."""

    def test_geometric_feasibility_filter_returns_correct_subset(self):
        """
        Test that the geometric feasibility filter correctly identifies candidates
        within the tolerance factor range [0.8, 1.1].
        
        This test creates a synthetic dataframe with known tolerance factors:
        - One clearly stable (t=0.95)
        - One clearly unstable (t=1.2)
        - One borderline stable (t=0.85)
        - One borderline unstable (t=0.75)
        - One exactly on the boundary (t=0.8)
        - One exactly on the upper boundary (t=1.1)
        """
        # Create a mock dataset with pre-calculated tolerance factors
        # We will inject the 'tolerance_factor' column directly to avoid dependency
        # on complex ionic radius lookups for this specific unit test,
        # focusing on the filter logic itself.
        
        data = {
            'A': ['Ba', 'Cs', 'Sr', 'K', 'Rb', 'Ba'],
            'B': ['Ti', 'Zr', 'Hf', 'Sn', 'Ge', 'Ti'],
            'X': ['O', 'O', 'O', 'O', 'O', 'O'],
            'formula': ['BaTiO3', 'CsZrO3', 'SrHfO3', 'KSnO3', 'RbGeO3', 'BaTiO3'],
            'tolerance_factor': [0.95, 1.20, 0.85, 0.75, 0.80, 1.10]
        }
        
        df_input = pd.DataFrame(data)
        
        # Define the expected stable indices based on 0.8 <= t <= 1.1
        # 0.95 (keep), 1.20 (drop), 0.85 (keep), 0.75 (drop), 0.80 (keep), 1.10 (keep)
        expected_stable_formulas = ['BaTiO3', 'SrHfO3', 'RbGeO3', 'BaTiO3']
        
        # Run the filter
        df_filtered = filter_geometric_feasibility(df_input)
        
        # Assertions
        assert isinstance(df_filtered, pd.DataFrame), "Filter should return a DataFrame"
        assert len(df_filtered) == 4, f"Expected 4 stable candidates, got {len(df_filtered)}"
        
        # Verify the specific formulas are kept
        assert list(df_filtered['formula']) == expected_stable_formulas, \
            f"Expected {expected_stable_formulas}, got {list(df_filtered['formula'])}"
        
        # Verify all tolerance factors in the result are within range
        assert all((df_filtered['tolerance_factor'] >= 0.8) & (df_filtered['tolerance_factor'] <= 1.1)), \
            "All returned candidates must have t in [0.8, 1.1]"
        
        # Verify the original dataframe was not modified (if passed by reference)
        # (In pandas, slicing returns a copy or view, but we check logic integrity)
        assert len(df_input) == 6, "Input dataframe should remain unchanged"

    def test_filter_handles_empty_input(self):
        """Test that the filter returns an empty DataFrame for empty input."""
        df_empty = pd.DataFrame(columns=['A', 'B', 'X', 'formula', 'tolerance_factor'])
        df_result = filter_geometric_feasibility(df_empty)
        assert len(df_result) == 0
        assert isinstance(df_result, pd.DataFrame)

    def test_filter_handles_all_unstable(self):
        """Test that the filter returns an empty DataFrame if all candidates are unstable."""
        data = {
            'A': ['Cs', 'K'],
            'B': ['Zr', 'Sn'],
            'X': ['O', 'O'],
            'formula': ['CsZrO3', 'KSnO3'],
            'tolerance_factor': [1.3, 0.6]
        }
        df_input = pd.DataFrame(data)
        df_result = filter_geometric_feasibility(df_input)
        assert len(df_result) == 0

    def test_filter_boundaries_inclusive(self):
        """Test that the boundaries 0.8 and 1.1 are inclusive."""
        data = {
            'A': ['Ba', 'Cs'],
            'B': ['Ti', 'Zr'],
            'X': ['O', 'O'],
            'formula': ['BaTiO3', 'CsZrO3'],
            'tolerance_factor': [0.8, 1.1]
        }
        df_input = pd.DataFrame(data)
        df_result = filter_geometric_feasibility(df_input)
        assert len(df_result) == 2, "Boundaries 0.8 and 1.1 should be included"

    def test_filter_drops_outside_boundaries(self):
        """Test that values strictly outside [0.8, 1.1] are dropped."""
        data = {
            'A': ['Ba', 'Cs', 'Sr'],
            'B': ['Ti', 'Zr', 'Hf'],
            'X': ['O', 'O', 'O'],
            'formula': ['BaTiO3', 'CsZrO3', 'SrHfO3'],
            'tolerance_factor': [0.799, 1.101, 0.9]
        }
        df_input = pd.DataFrame(data)
        df_result = filter_geometric_feasibility(df_input)
        assert len(df_result) == 1
        assert df_result.iloc[0]['formula'] == 'SrHfO3'