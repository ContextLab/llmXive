import os
import sys
import tempfile
import json
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure src is in path for imports
src_path = Path(__file__).resolve().parent.parent.parent / "code" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from data.schema import DataVersion

class TestMergeLogicOnInChIKey:
    """
    Unit tests for merge logic on InChIKey (handling missing data/NaNs).
    Tests T011: [P] [US1] Unit test for merge logic on InChIKey.
    """

    @pytest.fixture
    def sample_structure_data(self):
        """
        Returns a DataFrame simulating processed structure data
        (SMILES -> InChIKey + Descriptors).
        """
        return pd.DataFrame({
            "InChIKey": [
                "BSYNRYMUTXBXSQ-UHFFFAOYSA-N", # Aspirin
                "LFQSCWFLJHTTHZ-UHFFFAOYSA-N", # Ethanol (no resistance data)
                "ZMXDDKWLCZADIW-UHFFFAOYSA-N", # Acetone (no resistance data)
                "XUJNEKJLAYXESH-UHFFFAOYSA-N", # Cysteine (no resistance data)
                "LXCFILQKKVIQHA-UHFFFAOYSA-N"  # Unknown drug (no resistance data)
            ],
            "SMILES": [
                "CC(=O)OC1=CC=CC=C1C(=O)O",
                "CCO",
                "CC(=O)C",
                "NC(C(=O)O)CS",
                "CC(C)N1C=CC(=O)C1=CC=C2C=CC=C3C4=CC=CC=C4C3=C21" # Dummy
            ],
            "MW": [180.16, 46.07, 58.08, 121.15, 300.00],
            "LogP": [1.19, -0.31, -0.24, -1.00, 4.50]
        })

    @pytest.fixture
    def sample_resistance_data(self):
        """
        Returns a DataFrame simulating NCBI Pathogen Detection resistance data.
        Includes a compound not in structure data (Ciprofloxacin) to test
        drop behavior (inner join) or NaN behavior (outer/left join).
        """
        return pd.DataFrame({
            "InChIKey": [
                "BSYNRYMUTXBXSQ-UHFFFAOYSA-N", # Matches Aspirin
                "EVKQYQXJZQJWQW-UHFFFAOYSA-N", # Ciprofloxacin (not in structure data)
                "KJADKLWNBVXGJW-UHFFFAOYSA-N"  # Vancomycin (not in structure data)
            ],
            "Organism": [
                "Escherichia coli",
                "Pseudomonas aeruginosa",
                "Staphylococcus aureus"
            ],
            "ResistanceFrequency": [0.15, 0.45, 0.82]
        })

    @pytest.fixture
    def sample_resistance_data_missing(self):
        """
        Returns resistance data with NaN values in the frequency column
        to test NaN handling during merge.
        """
        return pd.DataFrame({
            "InChIKey": [
                "BSYNRYMUTXBXSQ-UHFFFAOYSA-N", # Matches Aspirin
                "LFQSCWFLJHTTHZ-UHFFFAOYSA-N", # Matches Ethanol
            ],
            "Organism": [
                "Escherichia coli",
                "Salmonella enterica"
            ],
            "ResistanceFrequency": [0.15, np.nan] # Explicit NaN
        })

    def test_inner_join_excludes_non_matching_keys(self, sample_structure_data, sample_resistance_data):
        """
        Verifies that an inner join on InChIKey correctly excludes:
        1. Structures without matching resistance data.
        2. Resistance records without matching structures.
        """
        # Implementation of merge logic (simulating src/data/process.py logic)
        merged = pd.merge(
            sample_structure_data,
            sample_resistance_data,
            on="InChIKey",
            how="inner"
        )

        # Expect only Aspirin to match
        assert len(merged) == 1
        assert merged.loc[0, "InChIKey"] == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
        assert "ResistanceFrequency" in merged.columns
        assert merged.loc[0, "ResistanceFrequency"] == 0.15

        # Verify non-matches are gone
        assert "LFQSCWFLJHTTHZ-UHFFFAOYSA-N" not in merged["InChIKey"].values

    def test_left_join_preserves_all_structures_with_nan_for_missing(self, sample_structure_data, sample_resistance_data):
        """
        Verifies that a left join preserves all structure entries,
        filling missing resistance data with NaN.
        """
        merged = pd.merge(
            sample_structure_data,
            sample_resistance_data,
            on="InChIKey",
            how="left"
        )

        # Expect all 5 structures
        assert len(merged) == 5

        # Aspirin should have value
        aspirin_row = merged[merged["InChIKey"] == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"]
        assert aspirin_row["ResistanceFrequency"].iloc[0] == 0.15

        # Ethanol should be NaN
        ethanol_row = merged[merged["InChIKey"] == "LFQSCWFLJHTTHZ-UHFFFAOYSA-N"]
        assert pd.isna(ethanol_row["ResistanceFrequency"].iloc[0])

    def test_merge_handles_explicit_nan_in_source(self, sample_structure_data, sample_resistance_data_missing):
        """
        Verifies that if the source resistance data contains an explicit NaN,
        the merged result preserves that NaN and does not drop the row.
        """
        merged = pd.merge(
            sample_structure_data,
            sample_resistance_data_missing,
            on="InChIKey",
            how="left"
        )

        # Expect 2 matches (Aspirin and Ethanol)
        assert len(merged) == 2

        # Ethanol row should have NaN
        ethanol_row = merged[merged["InChIKey"] == "LFQSCWFLJHTTHZ-UHFFFAOYSA-N"]
        assert pd.isna(ethanol_row["ResistanceFrequency"].iloc[0])

    def test_merge_with_duplicate_keys_in_source(self, sample_structure_data):
        """
        Verifies behavior when resistance data has duplicate InChIKeys
        (e.g., multiple organisms for same compound), resulting in a cartesian product.
        """
        # Create resistance data with duplicate InChIKey
        duplicate_resistance = pd.DataFrame({
            "InChIKey": [
                "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                "BSYNRYMUTXBXSQ-UHFFFAOYSA-N" # Duplicate
            ],
            "Organism": ["E. coli", "S. aureus"],
            "ResistanceFrequency": [0.10, 0.20]
        })

        merged = pd.merge(
            sample_structure_data,
            duplicate_resistance,
            on="InChIKey",
            how="inner"
        )

        # Aspirin should now appear twice
        aspirin_rows = merged[merged["InChIKey"] == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"]
        assert len(aspirin_rows) == 2
        # Verify frequencies are 0.10 and 0.20
        assert 0.10 in aspirin_rows["ResistanceFrequency"].values
        assert 0.20 in aspirin_rows["ResistanceFrequency"].values

    def test_merge_preserves_original_columns(self, sample_structure_data, sample_resistance_data):
        """
        Verifies that original columns from both dataframes are preserved
        (excluding the join key which is shared).
        """
        merged = pd.merge(
            sample_structure_data,
            sample_resistance_data,
            on="InChIKey",
            how="inner"
        )

        # Check structure columns
        assert "MW" in merged.columns
        assert "LogP" in merged.columns
        assert "SMILES" in merged.columns

        # Check resistance columns
        assert "Organism" in merged.columns
        assert "ResistanceFrequency" in merged.columns

        # Ensure no suffixes were applied (since column names didn't clash except key)
        assert not any("_x" in col for col in merged.columns)
        assert not any("_y" in col for col in merged.columns)