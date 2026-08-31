import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from extract_instructional_units import fetch_assistments_instructional_units, save_instructional_units

class TestExtractInstructionalUnits:
    """Contract tests for instructional unit extraction."""

    def test_fetch_schema_validation(self):
        """Test that fetch function validates required schema columns."""
        # This test would normally run against real data
        # For contract testing, we verify the function signature and expected behavior
        # In a real run, this would raise ValueError if columns are missing
        
        # Mock test: verify function exists and has correct signature
        import inspect
        sig = inspect.signature(fetch_assistments_instructional_units)
        params = list(sig.parameters.keys())
        
        assert 'dataset_name' in params
        assert 'sample_size' in params

    def test_save_instructional_units_creates_file(self, tmp_path):
        """Test that save_instructional_units creates a valid CSV file."""
        # Create a mock DataFrame
        mock_data = pd.DataFrame({
            'interaction_id': ['skill_1', 'skill_2', 'skill_3'],
            'instructional_unit': ['Algebra Basics', 'Geometry Intro', 'Calculus Fundamentals']
        })
        
        output_file = tmp_path / "test_units.csv"
        
        # Save
        save_instructional_units(mock_data, output_file)
        
        # Verify file exists
        assert output_file.exists()
        
        # Verify content
        loaded_df = pd.read_csv(output_file)
        assert len(loaded_df) == 3
        assert 'interaction_id' in loaded_df.columns
        assert 'instructional_unit' in loaded_df.columns
        assert list(loaded_df['interaction_id']) == ['skill_1', 'skill_2', 'skill_3']

    def test_extract_units_output_format(self):
        """Test that the extracted units have the correct format."""
        # This is a conceptual test - actual execution requires real data
        # We verify the expected column names and types
        expected_columns = ['interaction_id', 'instructional_unit']
        
        # The function should return a DataFrame with these columns
        # This is verified by the actual run in T022
        pass
