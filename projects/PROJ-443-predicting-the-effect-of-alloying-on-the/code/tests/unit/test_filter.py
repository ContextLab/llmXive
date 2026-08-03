import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure imports work relative to the project root if run from tests/
# Assuming standard structure: code/tests/unit/test_filter.py
# imports from code.src.data.filter
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.filter import count_principal_elements, filter_hea_samples


class TestCountPrincipalElements:
    def test_simple_hea_composition(self):
        """Test counting elements in a standard 5-element HEA."""
        comp = {"Fe": 0.2, "Co": 0.2, "Ni": 0.2, "Cr": 0.2, "Mn": 0.2}
        assert count_principal_elements(comp, threshold=0.05) == 5

    def test_below_threshold(self):
        """Test that elements below threshold are not counted."""
        comp = {"Fe": 0.5, "Co": 0.04, "Ni": 0.04, "Cr": 0.04, "Mn": 0.04}
        assert count_principal_elements(comp, threshold=0.05) == 1

    def test_empty_composition(self):
        """Test handling of empty composition."""
        assert count_principal_elements({}, threshold=0.05) == 0

    def test_invalid_types(self):
        """Test handling of non-dict input."""
        assert count_principal_elements("Fe0.5Co0.5", threshold=0.05) == 0
        assert count_principal_elements(None, threshold=0.05) == 0


class TestFilterHEASamples:
    @pytest.fixture
    def sample_df(self):
        """Create a sample dataframe with mixed valid/invalid HEA samples."""
        data = {
            "Fe": [0.2, 0.5, 0.1, 0.2, 0.1],
            "Co": [0.2, 0.2, 0.1, 0.2, 0.1],
            "Ni": [0.2, 0.1, 0.1, 0.2, 0.1],
            "Cr": [0.2, 0.1, 0.1, 0.2, 0.1],
            "Mn": [0.2, 0.1, 0.1, 0.2, 0.1],
            "Bulk_Modulus": [150.0, 160.0, 140.0, np.nan, 155.0],
            "Material_ID": [1, 2, 3, 4, 5]
        }
        return pd.DataFrame(data)

    def test_filter_keeps_valid_hea(self, sample_df):
        """Test that valid HEAs (>=5 elements, valid target) are kept."""
        # Row 0: 5 elements, valid BM -> Keep
        # Row 1: 1 element (Fe), valid BM -> Drop
        # Row 2: 5 elements (0.1 each), valid BM -> Keep (0.1 >= 0.05)
        # Row 3: 5 elements, NaN BM -> Drop
        # Row 4: 5 elements (0.1 each), valid BM -> Keep
        
        filtered_df, stats = filter_hea_samples(sample_df, min_principal_elements=5, composition_threshold=0.05)
        
        assert len(filtered_df) == 3
        assert list(filtered_df["Material_ID"]) == [1, 3, 5]

    def test_filter_removes_invalid_target(self, sample_df):
        """Test that samples with NaN Bulk Modulus are removed."""
        filtered_df, _ = filter_hea_samples(sample_df)
        assert not filtered_df["Bulk_Modulus"].isna().any()

    def test_filter_removes_insufficient_elements(self, sample_df):
        """Test that samples with <5 principal elements are removed."""
        filtered_df, _ = filter_hea_samples(sample_df)
        # Row 1 had only 1 principal element
        assert 2 not in filtered_df["Material_ID"].values

    def test_stats_accuracy(self, sample_df):
        """Test that stats dictionary is accurate."""
        filtered_df, stats = filter_hea_samples(sample_df)
        assert stats["total"] == 5
        assert stats["filtered"] == 3
        assert stats["final_valid"] == 3

    def test_min_valid_samples_threshold(self, sample_df):
        """Test behavior when result is below min_valid_samples."""
        # Request min 10, get 3. Should return the 3 rows (pipeline handles the error).
        filtered_df, stats = filter_hea_samples(sample_df, min_valid_samples=10)
        assert len(filtered_df) == 3
        assert stats["final_valid"] == 3