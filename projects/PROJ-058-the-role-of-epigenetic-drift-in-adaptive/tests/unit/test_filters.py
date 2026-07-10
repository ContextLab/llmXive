"""Unit tests for global filters (T018)."""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocess.filters import (
    is_model_organism,
    normalize_organism_name,
    filter_by_organism,
    filter_by_global_methylation_level,
    apply_global_filters
)


class TestOrganismFilter:
    """Tests for organism filtering logic."""

    def test_normalize_organism_name(self):
        """Test organism name normalization."""
        assert normalize_organism_name("Mus musculus") == "mouse"
        assert normalize_organism_name("HOMO SAPIENS") == "human"
        assert normalize_organism_name("caenorhabditis elegans") == "c. elegans"
        assert normalize_organism_name("Drosophila melanogaster") == "drosophila"
        assert normalize_organism_name("") == ""
        assert normalize_organism_name(None) == ""

    def test_is_model_organism(self):
        """Test model organism detection."""
        # Should pass
        assert is_model_organism("Mus musculus") is True
        assert is_model_organism("human") is True
        assert is_model_organism("C. elegans") is True
        assert is_model_organism("Drosophila") is True
        assert is_model_organism("mouse") is True

        # Should fail
        assert is_model_organism("Zea mays") is False
        assert is_model_organism("Arabidopsis thaliana") is False
        assert is_model_organism("") is False

    def test_filter_by_organism(self):
        """Test filtering dataframe by organism."""
        df = pd.DataFrame({
            "gene_id": ["g1", "g2", "g3", "g4"],
            "organism": ["Mus musculus", "Zea mays", "Human", "C. elegans"]
        })

        filtered_df, excluded = filter_by_organism(df, "organism")

        # Should keep 3 rows (mouse, human, c. elegans)
        assert len(filtered_df) == 3
        assert "Zea mays" not in filtered_df["organism"].values
        assert "zea mays" in [o.lower() for o in excluded]

    def test_filter_by_organism_missing_column(self):
        """Test behavior when organism column is missing."""
        df = pd.DataFrame({
            "gene_id": ["g1", "g2"],
            "value": [1, 2]
        })

        filtered_df, excluded = filter_by_organism(df, "organism")

        # Should return original dataframe
        assert len(filtered_df) == 2
        assert len(excluded) == 0


class TestMethylationFilter:
    """Tests for methylation level filtering."""

    def test_filter_by_global_methylation_level(self):
        """Test filtering by methylation threshold."""
        df = pd.DataFrame({
            "gene_id": ["g1", "g2", "g3", "g4"],
            "mean_methylation": [0.05, 0.005, 0.1, 0.01]
        })

        filtered_df, stats = filter_by_global_methylation_level(df, "mean_methylation", threshold=0.01)

        # Should keep 3 rows (0.05, 0.1, 0.01 are >= 0.01)
        assert len(filtered_df) == 3
        assert "g2" not in filtered_df["gene_id"].values
        assert stats["excluded_count"] == 1
        assert stats["threshold_used"] == 0.01

    def test_filter_by_global_methylation_level_with_nan(self):
        """Test filtering handles NaN values correctly."""
        df = pd.DataFrame({
            "gene_id": ["g1", "g2", "g3"],
            "mean_methylation": [0.05, np.nan, 0.1]
        })

        filtered_df, stats = filter_by_global_methylation_level(df, "mean_methylation", threshold=0.01)

        # Should keep all rows (NaN is not excluded)
        assert len(filtered_df) == 3

    def test_filter_by_global_methylation_level_missing_column(self):
        """Test behavior when methylation column is missing."""
        df = pd.DataFrame({
            "gene_id": ["g1", "g2"],
            "value": [1, 2]
        })

        filtered_df, stats = filter_by_global_methylation_level(df, "mean_methylation", threshold=0.01)

        # Should return original dataframe
        assert len(filtered_df) == 2
        assert stats["excluded_count"] == 0


class TestApplyGlobalFilters:
    """Tests for combined filter application."""

    def test_apply_global_filters(self):
        """Test applying both organism and methylation filters."""
        methyl_df = pd.DataFrame({
            "gene_id": ["g1", "g2", "g3"],
            "organism": ["Mus musculus", "Zea mays", "C. elegans"],
            "mean_methylation": [0.05, 0.005, 0.1]
        })

        rna_df = pd.DataFrame({
            "gene_id": ["g1", "g2", "g3"],
            "organism": ["Mus musculus", "Zea mays", "C. elegans"],
            "expression": [10, 20, 30]
        })

        filtered_methyl, filtered_rna, stats = apply_global_filters(
            methyl_df, rna_df,
            methyl_org_col="organism",
            rna_org_col="organism",
            methyl_col="mean_methylation",
            methylation_threshold=0.01
        )

        # Check organism filtering worked
        assert len(filtered_methyl) == 2  # Removed Zea mays
        assert len(filtered_rna) == 2
        assert "Zea mays" not in filtered_methyl["organism"].values

        # Check methylation filtering worked
        assert len(filtered_methyl) == 2  # g2 has 0.005 < 0.01, but g2 was already removed by organism filter
        # Actually, g2 was removed by organism filter, so only g1 and g3 remain
        # g1: 0.05 >= 0.01 -> keep
        # g3: 0.1 >= 0.01 -> keep
        # So final count is 2

        assert "organism_filter" in stats
        assert "methylation_filter" in stats

    def test_apply_global_filters_missing_columns(self):
        """Test handling of missing columns."""
        methyl_df = pd.DataFrame({
            "gene_id": ["g1", "g2"],
            "value": [1, 2]
        })

        rna_df = pd.DataFrame({
            "gene_id": ["g1", "g2"],
            "value": [3, 4]
        })

        # Should not raise error
        filtered_methyl, filtered_rna, stats = apply_global_filters(
            methyl_df, rna_df,
            methyl_org_col="organism",
            rna_org_col="organism",
            methyl_col="mean_methylation"
        )

        # Should return original dataframes
        assert len(filtered_methyl) == 2
        assert len(filtered_rna) == 2
        assert stats["organism_filter"]["methyl"]["excluded_organisms"] == []
        assert stats["methylation_filter"]["excluded_count"] == 0
