import pytest
import pandas as pd
import json
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis import add_metadata_flag, ASSOCIATIONAL_FLAG

class TestMetadataFlag:
    """Test contract for FR-003.1: Associational analysis metadata flag."""

    def test_flag_column_added(self):
        """Verify that the metadata flag column is added to the output dataframe."""
        # Create a test dataframe
        test_df = pd.DataFrame({
            "sample_id": [1, 2, 3],
            "pH": [6.5, 7.0, 7.5],
            "shannon": [2.1, 2.5, 2.8]
        })

        # Apply the flag
        result_df = add_metadata_flag(test_df)

        # Assert the column exists
        assert ASSOCIATIONAL_FLAG in result_df.columns, \
            f"Column '{ASSOCIATIONAL_FLAG}' not found in output dataframe"

    def test_flag_values_are_true(self):
        """Verify that all flag values are set to True."""
        test_df = pd.DataFrame({
            "sample_id": [1, 2, 3],
            "value": [10, 20, 30]
        })

        result_df = add_metadata_flag(test_df)

        # Assert all values in the flag column are True
        assert all(result_df[ASSOCIATIONAL_FLAG] == True), \
            "Not all flag values are True"

    def test_metadata_json_compliance(self):
        """Verify the metadata JSON file contains the required compliance info."""
        metadata_path = Path("data/processed/analysis_metadata.json")
        
        if not metadata_path.exists():
            pytest.skip("Metadata file not generated yet - run analysis pipeline first")

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        # Check for FR-003.1 compliance section
        assert "fr_003_1_compliance" in metadata, \
            "Metadata missing 'fr_003_1_compliance' section"

        compliance = metadata["fr_003_1_compliance"]
        assert compliance["flag_description"] == ASSOCIATIONAL_FLAG, \
            "Flag description does not match required string"
        
        assert compliance["applied"] is True, \
            "Flag applied status is not True"