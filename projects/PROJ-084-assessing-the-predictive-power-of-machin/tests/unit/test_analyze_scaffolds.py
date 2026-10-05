"""
Unit tests for T022a: analyze_scaffolds.py
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# Import the module under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))
from preprocessing.analyze_scaffolds import (
    load_scaffold_groups,
    load_batched_reactions,
    analyze_cross_class_scaffolds,
    save_cross_class_scaffolds
)

class TestLoadScaffoldGroups:
    def test_load_valid_file(self, tmp_path):
        """Test loading a valid scaffold groups file."""
        # Create a valid parquet file
        data = {
            "scaffold_id": ["s1", "s2", "s3"],
            "reaction_class": ["class_a", "class_b", "class_a"]
        }
        df = pd.DataFrame(data)
        test_file = tmp_path / "scaffold_groups.parquet"
        df.to_parquet(test_file)

        result = load_scaffold_groups(test_file)
        assert len(result) == 3
        assert "scaffold_id" in result.columns
        assert "reaction_class" in result.columns

    def test_missing_file(self, tmp_path):
        """Test error when file does not exist."""
        with pytest.raises(FileNotFoundError):
            load_scaffold_groups(tmp_path / "nonexistent.parquet")

    def test_missing_columns(self, tmp_path):
        """Test error when required columns are missing."""
        data = {"scaffold_id": ["s1"]}
        df = pd.DataFrame(data)
        test_file = tmp_path / "scaffold_groups.parquet"
        df.to_parquet(test_file)

        with pytest.raises(ValueError, match="missing required columns"):
            load_scaffold_groups(test_file)

class TestLoadBatchedReactions:
    def test_load_valid_file(self, tmp_path):
        """Test loading a valid batched reactions file."""
        data = {
            "reaction_smiles": ["A>>B", "C>>D"],
            "reaction_class": ["class_a", "class_b"]
        }
        df = pd.DataFrame(data)
        test_file = tmp_path / "batched_reactions.parquet"
        df.to_parquet(test_file)

        result = load_batched_reactions(test_file)
        assert len(result) == 2
        assert "reaction_class" in result.columns

    def test_missing_reaction_class(self, tmp_path):
        """Test error when reaction_class column is missing."""
        data = {"reaction_smiles": ["A>>B"]}
        df = pd.DataFrame(data)
        test_file = tmp_path / "batched_reactions.parquet"
        df.to_parquet(test_file)

        with pytest.raises(ValueError, match="missing 'reaction_class' column"):
            load_batched_reactions(test_file)

class TestAnalyzeCrossClassScaffolds:
    def test_no_cross_class_scaffolds(self):
        """Test when all scaffolds belong to a single reaction class."""
        scaffold_df = pd.DataFrame({
            "scaffold_id": ["s1", "s2", "s3"],
            "reaction_class": ["class_a", "class_b", "class_c"]
        })
        reactions_df = pd.DataFrame({
            "reaction_smiles": ["A>>B", "C>>D", "E>>F"],
            "reaction_class": ["class_a", "class_b", "class_c"]
        })

        result = analyze_cross_class_scaffolds(scaffold_df, reactions_df)
        assert result == []

    def test_with_cross_class_scaffolds(self):
        """Test when some scaffolds belong to multiple reaction classes."""
        scaffold_df = pd.DataFrame({
            "scaffold_id": ["s1", "s1", "s2", "s3", "s3"],
            "reaction_class": ["class_a", "class_b", "class_c", "class_d", "class_d"]
        })
        reactions_df = pd.DataFrame({
            "reaction_smiles": ["A>>B", "C>>D", "E>>F", "G>>H", "I>>J"],
            "reaction_class": ["class_a", "class_b", "class_c", "class_d", "class_d"]
        })

        result = analyze_cross_class_scaffolds(scaffold_df, reactions_df)
        assert result == ["s1"]

    def test_multiple_cross_class_scaffolds(self):
        """Test multiple scaffolds with multiple reaction classes."""
        scaffold_df = pd.DataFrame({
            "scaffold_id": ["s1", "s1", "s2", "s2", "s3"],
            "reaction_class": ["class_a", "class_b", "class_c", "class_d", "class_e"]
        })
        reactions_df = pd.DataFrame({
            "reaction_smiles": ["A>>B"] * 5,
            "reaction_class": ["class_a", "class_b", "class_c", "class_d", "class_e"]
        })

        result = analyze_cross_class_scaffolds(scaffold_df, reactions_df)
        assert set(result) == {"s1", "s2"}

class TestSaveCrossClassScaffolds:
    def test_save_and_load(self, tmp_path):
        """Test saving and verifying the output JSON."""
        cross_class_ids = ["s1", "s2", "s3"]
        output_file = tmp_path / "cross_class_scaffolds.json"

        save_cross_class_scaffolds(cross_class_ids, output_file)

        assert output_file.exists()
        with open(output_file, "r") as f:
            data = json.load(f)

        assert data["count"] == 3
        assert data["scaffold_ids"] == ["s1", "s2", "s3"]
        assert "generated_at" in data
        assert "note" in data