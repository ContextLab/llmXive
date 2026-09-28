import pytest
import pandas as pd
import os
from pathlib import Path
from typing import List, Dict, Any

class TestDiffAbundanceSchema:
    """Contract tests for differential abundance output schema."""

    @pytest.fixture
    def sample_diff_ab_df(self):
        """Sample DataFrame for differential abundance results."""
        data = {
            "taxon": ["TaxonA", "TaxonB"],
            "method": ["ANCOM", "DESeq2"],
            "q_value": [0.01, 0.03],
            "effect_size": [0.5, -0.4],
            "direction": ["up", "down"],
            "power_flag": [False, True]
        }
        return pd.DataFrame(data)

    def test_required_columns_exist(self, sample_diff_ab_df):
        """Verify all required columns are present."""
        required_columns = ["taxon", "method", "q_value", "effect_size", "direction"]
        for col in required_columns:
            assert col in sample_diff_ab_df.columns, f"Missing column: {col}"

    def test_data_types(self, sample_diff_ab_df):
        """Verify data types are correct."""
        assert sample_diff_ab_df["q_value"].dtype in ["float64", "float32"]
        assert sample_diff_ab_df["effect_size"].dtype in ["float64", "float32"]
        assert sample_diff_ab_df["direction"].dtype == "object"

    def test_q_value_range(self, sample_diff_ab_df):
        """Verify q_values are between 0 and 1."""
        assert all(0 <= x <= 1 for x in sample_diff_ab_df["q_value"])

class TestReplicationStatusSchema:
    """Contract tests for replication status output schema."""

    @pytest.fixture
    def sample_replication_df(self):
        """Sample DataFrame for replication status results."""
        data = {
            "taxon": ["TaxonA", "TaxonB"],
            "method": ["MaAsLin2", "ANCOM"],
            "agp_q_value": [0.01, 0.02],
            "ukbb_q_value": [0.03, 0.04],
            "agp_effect_size": [0.5, -0.3],
            "ukbb_effect_size": [0.4, -0.2],
            "replication_status": ["replicated", "cohort-specific"],
            "power_flag": [False, True],
            "diff_abundance_status": ["replicated", "non-replicable"]
        }
        return pd.DataFrame(data)

    def test_required_columns_exist(self, sample_replication_df):
        """Verify all required columns are present."""
        required_columns = [
            "taxon", "method", "agp_q_value", "ukbb_q_value",
            "agp_effect_size", "ukbb_effect_size", "replication_status",
            "power_flag", "diff_abundance_status"
        ]
        for col in required_columns:
            assert col in sample_replication_df.columns, f"Missing column: {col}"

    def test_replication_status_values(self, sample_replication_df):
        """Verify replication_status contains valid values."""
        valid_values = ["replicated", "non-replicable", "cohort-specific"]
        for status in sample_replication_df["replication_status"]:
            assert status in valid_values, f"Invalid status: {status}"

    def test_diff_abundance_status_values(self, sample_replication_df):
        """Verify diff_abundance_status contains valid values."""
        valid_values = ["replicated", "non-replicable", "cohort-specific"]
        for status in sample_replication_df["diff_abundance_status"]:
            assert status in valid_values, f"Invalid status: {status}"
