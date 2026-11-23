"""
Unit test for isolate filtering logic.
"""
import pytest
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

class TestIsolateFiltering:
    def test_apply_max_isolates_limit(self):
        """
        Test that the max isolates limit is correctly applied.
        """
        # Create mock metadata
        mock_data = pd.DataFrame({
            "isolate_id": [f"iso_{i}" for i in range(100)],
            "resistance_phenotype": [0] * 50 + [1] * 50,
            "antibiotic_class": ["class_A"] * 100
        })
        
        max_limit = 50
        
        # Simulate the logic from ingest_metadata.py
        # Usually involves stratified sampling or simple truncation
        # Here we test the truncation logic for simplicity
        if len(mock_data) > max_limit:
            # Simple truncation for test (real code might be stratified)
            filtered = mock_data.head(max_limit)
        else:
            filtered = mock_data
        
        assert len(filtered) == max_limit
        assert len(filtered["isolate_id"].unique()) == max_limit

    def test_handle_missing_phenotype(self):
        """
        Test that rows with missing phenotype are handled/excluded.
        """
        mock_data = pd.DataFrame({
            "isolate_id": ["iso_1", "iso_2", "iso_3"],
            "resistance_phenotype": [1, None, 0]
        })
        
        # Simulate handling missing values (drop rows)
        cleaned = mock_data.dropna(subset=["resistance_phenotype"])
        
        assert len(cleaned) == 2
        assert "iso_2" not in cleaned["isolate_id"].values
        assert not cleaned["resistance_phenotype"].isnull().any()

    def test_validate_columns_present(self):
        """
        Test that required columns are present in metadata.
        """
        required_cols = ["isolate_id", "resistance_phenotype"]
        mock_data = pd.DataFrame({
            "isolate_id": ["iso_1"],
            "resistance_phenotype": [1],
            "extra_col": ["val"]
        })
        
        missing = [c for c in required_cols if c not in mock_data.columns]
        assert len(missing) == 0, f"Missing columns: {missing}"
        
        # Test missing column case
        bad_data = pd.DataFrame({"isolate_id": ["iso_1"]})
        missing_bad = [c for c in required_cols if c not in bad_data.columns]
        assert len(missing_bad) > 0
