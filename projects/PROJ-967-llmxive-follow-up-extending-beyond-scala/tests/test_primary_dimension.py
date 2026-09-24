"""
Unit tests for Primary Dimension Identification (T014)
"""
import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the module functions
# Since we are running tests from the project root, we need to ensure code/ is in path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from primary_dimension import (
    derive_primary_dimension,
    process_dataframe_primary_dimensions,
    RULE_HASH,
    DERIVATION_RULE,
    NUM_DIMENSIONS
)


class TestDerivePrimaryDimension:
    def test_hash_stability(self):
        """Ensure the same species_id always produces the same dimension."""
        sid = "species_123"
        dim1 = derive_primary_dimension(sid)
        dim2 = derive_primary_dimension(sid)
        assert dim1 == dim2
        assert 0 <= dim1 < NUM_DIMENSIONS

    def test_different_ids_different_dims(self):
        """Different species_ids should likely produce different dimensions."""
        dim1 = derive_primary_dimension("species_A")
        dim2 = derive_primary_dimension("species_B")
        # While collisions are possible, we just check they are valid integers
        assert isinstance(dim1, int)
        assert isinstance(dim2, int)
        assert 0 <= dim1 < NUM_DIMENSIONS
        assert 0 <= dim2 < NUM_DIMENSIONS

    def test_integer_id(self):
        """Test with integer species_id."""
        dim = derive_primary_dimension(42)
        assert isinstance(dim, int)
        assert 0 <= dim < NUM_DIMENSIONS

class TestProcessDataFrame:
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            "sample_id": ["s1", "s2", "s3"],
            "species_id": ["cat", "dog", "bird"],
            "other_col": [1, 2, 3]
        })

    def test_process_valid_data(self, sample_df):
        """Test processing a dataframe with valid species_ids."""
        df_out, lineage, exclusions = process_dataframe_primary_dimensions(sample_df, None)

        assert "primary_dimension" in df_out.columns
        assert len(df_out) == 3
        assert len(lineage) == 3
        assert len(exclusions) == 0

        for entry in lineage:
            assert entry["derivation_rule"] == DERIVATION_RULE
            assert entry["derivation_rule_hash"] == RULE_HASH
            assert entry["source_type"] == "metadata"
            assert 0 <= entry["dimension"] < NUM_DIMENSIONS

    def test_missing_species_id_raises(self):
        """Test that missing species_id column raises an error."""
        df = pd.DataFrame({"sample_id": ["s1"]})
        with pytest.raises(ValueError, match="must contain 'species_id'"):
            process_dataframe_primary_dimensions(df, None)

    def test_auto_generated_sample_id(self):
        """Test behavior when sample_id is missing."""
        df = pd.DataFrame({"species_id": ["cat", "dog"]})
        # This should not raise, but generate IDs
        df_out, lineage, exclusions = process_dataframe_primary_dimensions(df, None)
        assert "sample_id" in df_out.columns
        assert len(lineage) == 2