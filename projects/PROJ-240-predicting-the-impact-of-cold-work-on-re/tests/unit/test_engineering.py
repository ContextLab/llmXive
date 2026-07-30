"""
TDD Unit Test for Interaction Feature Engineering (Task T011).

This test verifies that interaction features (cold_work * composition) are 
correctly calculated in the engineer.py module.

Per TDD requirements, this test is written to FAIL initially until 
code/engineer.py is implemented with the correct logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

# Import the target function (This will fail if engineer.py is not implemented)
try:
    from engineer import create_interaction_features
except ImportError:
    # If not implemented yet, we define a stub to ensure the test framework 
    # recognizes the test, but the test itself will fail as expected for TDD.
    # In a real TDD flow, we run this, see the failure, then implement.
    def create_interaction_features(df):
        raise NotImplementedError("T011 Implementation Pending: engineer.py not yet created.")

class TestInteractionFeatureEngineering:
    """Tests for interaction feature calculation logic."""

    def test_interaction_features_exist(self):
        """
        Test that the output DataFrame contains the expected interaction columns.
        Expected columns: 
          - cold_work * Mn_content
          - cold_work * Mg_content
          - cold_work * Si_content
          - cold_work * Cu_content
        """
        # Arrange: Create a minimal valid DataFrame
        data = {
            "cold_work": [50.0, 60.0, 70.0],
            "Mn_content": [1.0, 2.0, 3.0],
            "Mg_content": [0.5, 1.0, 1.5],
            "Si_content": [0.3, 0.6, 0.9],
            "Cu_content": [0.1, 0.2, 0.3],
            "annealing_temp": [300, 350, 400],
            "time_to_peak": [100, 200, 300]
        }
        df = pd.DataFrame(data)

        # Act
        result = create_interaction_features(df)

        # Assert
        expected_interactions = [
            "cold_work * Mn_content",
            "cold_work * Mg_content",
            "cold_work * Si_content",
            "cold_work * Cu_content"
        ]

        for col in expected_interactions:
            assert col in result.columns, f"Missing interaction column: {col}"

    def test_interaction_values_correctness(self):
        """
        Test that the calculated interaction values are mathematically correct.
        Verifies: cold_work * Mn_content == result['cold_work * Mn_content']
        """
        # Arrange
        data = {
            "cold_work": [10.0, 20.0],
            "Mn_content": [2.0, 4.0],
            "Mg_content": [1.0, 2.0],
            "Si_content": [0.5, 1.0],
            "Cu_content": [0.2, 0.4],
            "annealing_temp": [300, 350],
            "time_to_peak": [100, 200]
        }
        df = pd.DataFrame(data)

        # Act
        result = create_interaction_features(df)

        # Assert
        # Check first row: 10.0 * 2.0 = 20.0
        assert result.iloc[0]["cold_work * Mn_content"] == pytest.approx(20.0)
        # Check second row: 20.0 * 4.0 = 80.0
        assert result.iloc[1]["cold_work * Mn_content"] == pytest.approx(80.0)
        
        # Verify Mg interaction: 10.0 * 1.0 = 10.0
        assert result.iloc[0]["cold_work * Mg_content"] == pytest.approx(10.0)

    def test_original_columns_preserved(self):
        """
        Test that the original input columns are preserved in the output.
        """
        data = {
            "cold_work": [50.0],
            "Mn_content": [1.0],
            "Mg_content": [0.5],
            "Si_content": [0.3],
            "Cu_content": [0.1],
            "annealing_temp": [300],
            "time_to_peak": [100]
        }
        df = pd.DataFrame(data)
        original_columns = list(df.columns)

        result = create_interaction_features(df)

        for col in original_columns:
            assert col in result.columns, f"Original column {col} was dropped."

    def test_no_null_values_in_interactions(self):
        """
        Test that the generated interaction features contain no null values.
        """
        data = {
            "cold_work": [50.0, 60.0],
            "Mn_content": [1.0, 2.0],
            "Mg_content": [0.5, 1.0],
            "Si_content": [0.3, 0.6],
            "Cu_content": [0.1, 0.2],
            "annealing_temp": [300, 350],
            "time_to_peak": [100, 200]
        }
        df = pd.DataFrame(data)

        result = create_interaction_features(df)

        interaction_cols = [
            "cold_work * Mn_content",
            "cold_work * Mg_content",
            "cold_work * Si_content",
            "cold_work * Cu_content"
        ]

        for col in interaction_cols:
            assert result[col].isnull().sum() == 0, f"Null values found in {col}"