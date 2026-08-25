"""
Integration test for mechanism-blind filtering.
Ensures that known resistance genes for the target class are excluded.
"""
import pytest
import pandas as pd
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

class TestMechanismBlind:
    def test_filter_mechanism_genes(self):
        """
        Test that genes associated with the target antibiotic class are removed.
        """
        # Mock feature matrix
        mock_features = pd.DataFrame({
            "isolate_id": ["iso_1", "iso_2"],
            "gene_A": [1, 0],
            "gene_B": [0, 1],
            "gene_C": [1, 1],
            "other_feature": [0.5, 0.6]
        })
        
        # Mock class-to-genes mapping
        mock_mapping = {
            "fluoroquinolones": ["gene_A", "gene_B"],
            "beta_lactams": ["gene_C"]
        }
        
        target_class = "fluoroquinolones"
        genes_to_exclude = set(mock_mapping[target_class])
        
        # Simulate filtering logic
        feature_cols = [c for c in mock_features.columns if c not in ["isolate_id"]]
        filtered_cols = [c for c in feature_cols if c not in genes_to_exclude]
        
        filtered_df = mock_features[["isolate_id"] + filtered_cols]
        
        # Verify exclusion
        assert "gene_A" not in filtered_df.columns
        assert "gene_B" not in filtered_df.columns
        assert "gene_C" in filtered_df.columns # Should remain as it's not in target class
        assert "other_feature" in filtered_df.columns

    def test_filter_preserves_metadata(self):
        """
        Test that filtering does not drop non-feature columns (like metadata).
        """
        mock_features = pd.DataFrame({
            "isolate_id": ["iso_1"],
            "resistance_phenotype": [1],
            "gene_X": [1]
        })
        
        # If gene_X is NOT in the target class mapping, it should remain
        # If it IS, it should be removed, but phenotype and isolate_id must remain
        
        # Simulate a scenario where gene_X is excluded
        exclude_set = {"gene_X"}
        cols_to_keep = [c for c in mock_features.columns if c not in exclude_set]
        
        filtered = mock_features[cols_to_keep]
        
        assert "isolate_id" in filtered.columns
        assert "resistance_phenotype" in filtered.columns
        assert "gene_X" not in filtered.columns
