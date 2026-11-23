import pytest
import pandas as pd
import hashlib
import json
import os
import sys
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from primary_dimension_util import (
    derive_primary_dimension_from_metadata,
    process_dataframe_primary_dimensions,
    get_derivation_rule_hash,
    RUBRIC_DIMENSIONS
)

class TestPrimaryDimensionDerivation:
    def test_derive_from_nested_metadata(self):
        """Test extraction from prompt_metadata.primary_dimension"""
        row = {
            "prompt": "A cat",
            "prompt_metadata": {
                "primary_dimension": "Alignment"
            }
        }
        result = derive_primary_dimension_from_metadata(row)
        assert result == "Alignment"

    def test_derive_from_direct_column(self):
        """Test extraction from direct primary_dimension column"""
        row = {
            "prompt": "A dog",
            "primary_dimension": "Realism"
        }
        result = derive_primary_dimension_from_metadata(row)
        assert result == "Realism"

    def test_derive_from_prompt_hash(self):
        """Test deterministic derivation from prompt text when metadata is missing"""
        row = {
            "prompt": "Unique test prompt for hashing",
            "other_field": "value"
        }
        result = derive_primary_dimension_from_metadata(row)
        assert result in RUBRIC_DIMENSIONS

    def test_derive_returns_none_when_missing_all(self):
        """Test that None is returned if no source is available"""
        row = {
            "other_field": "value"
        }
        result = derive_primary_dimension_from_metadata(row)
        assert result is None

    def test_hash_consistency(self):
        """Test that the same prompt always yields the same dimension"""
        prompt = "Consistent prompt test"
        row1 = {"prompt": prompt}
        row2 = {"prompt": prompt}
        assert derive_primary_dimension_from_metadata(row1) == derive_primary_dimension_from_metadata(row2)

class TestProcessDataFrame:
    def test_process_with_valid_metadata(self):
        """Test processing a dataframe with valid metadata"""
        data = [
            {"sample_id": "1", "prompt": "Test 1", "prompt_metadata": {"primary_dimension": "Aesthetics"}},
            {"sample_id": "2", "prompt": "Test 2", "primary_dimension": "Plausibility"}
        ]
        df = pd.DataFrame(data)
        filtered_df, lineage, exclusions = process_dataframe_primary_dimensions(df)

        assert len(filtered_df) == 2
        assert len(exclusions) == 0
        assert len(lineage) == 2
        assert filtered_df.loc[0, "primary_dimension"] == "Aesthetics"
        assert filtered_df.loc[1, "primary_dimension"] == "Plausibility"

    def test_process_with_missing_metadata(self):
        """Test that samples with missing metadata are excluded"""
        data = [
            {"sample_id": "1", "prompt": "Test 1", "prompt_metadata": {"primary_dimension": "Alignment"}},
            {"sample_id": "2", "prompt": "Test 2"},  # Missing metadata
            {"sample_id": "3", "prompt": "Test 3", "primary_dimension": "Realism"}
        ]
        df = pd.DataFrame(data)
        filtered_df, lineage, exclusions = process_dataframe_primary_dimensions(df)

        assert len(filtered_df) == 2
        assert len(exclusions) == 1
        assert exclusions[0]["sample_id"] == "2"
        assert exclusions[0]["reason"] == "missing_metadata"
        assert "timestamp" in exclusions[0]

    def test_derivation_rule_hash_in_lineage(self):
        """Test that the lineage report contains the correct derivation rule hash"""
        data = [
            {"sample_id": "1", "prompt": "Test 1", "prompt_metadata": {"primary_dimension": "Alignment"}}
        ]
        df = pd.DataFrame(data)
        _, lineage, _ = process_dataframe_primary_dimensions(df)

        expected_hash = get_derivation_rule_hash()
        assert lineage[0]["derivation_rule_hash"] == expected_hash
        assert lineage[0]["source_type"] == "metadata"
        assert lineage[0]["dimension"] == "Alignment"

    def test_empty_dataframe(self):
        """Test processing an empty dataframe"""
        df = pd.DataFrame(columns=["sample_id", "prompt"])
        filtered_df, lineage, exclusions = process_dataframe_primary_dimensions(df)
        assert len(filtered_df) == 0
        assert len(lineage) == 0
        assert len(exclusions) == 0
