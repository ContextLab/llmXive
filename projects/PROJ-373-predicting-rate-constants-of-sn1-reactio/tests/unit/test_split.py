import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data.split import stratified_split

class TestStratifiedSplit:
    @pytest.fixture
    def mock_data(self):
        """Create a mock dataset with balanced substrate classes."""
        n_samples = 100
        data = {
            "smiles": [f"C{i}" for i in range(n_samples)],
            "rate_constant": np.random.rand(n_samples) * 10,
            "substrate_class": ["secondary" if i % 2 == 0 else "tertiary" for i in range(n_samples)]
        }
        return pd.DataFrame(data)

    def test_split_ratios(self, mock_data):
        """Test that the split ratios are approximately correct."""
        train, val, test = stratified_split(mock_data, random_state=42)
        
        total = len(mock_data)
        assert abs(len(train) - 0.7 * total) < 0.05 * total, "Train ratio is incorrect"
        assert abs(len(val) - 0.15 * total) < 0.05 * total, "Val ratio is incorrect"
        assert abs(len(test) - 0.15 * total) < 0.05 * total, "Test ratio is incorrect"
        assert len(train) + len(val) + len(test) == total, "Total rows mismatch"

    def test_stratification_preserved(self, mock_data):
        """Test that substrate class distribution is preserved in splits."""
        train, val, test = stratified_split(mock_data, random_state=42)
        
        # Check that both classes exist in all splits
        for split_name, split_df in [("train", train), ("val", val), ("test", test)]:
            unique_classes = split_df["substrate_class"].unique()
            assert len(unique_classes) == 2, f"{split_name} split missing a class"
            assert "secondary" in unique_classes, f"{split_name} missing secondary"
            assert "tertiary" in unique_classes, f"{split_name} missing tertiary"

    def test_invalid_column(self, mock_data):
        """Test that an error is raised if the stratification column is missing."""
        df_no_class = mock_data.drop(columns=["substrate_class"])
        with pytest.raises(ValueError, match="Stratification column"):
            stratified_split(df_no_class, substrate_col="missing_col")

    def test_reproducibility(self, mock_data):
        """Test that the split is reproducible with the same random state."""
        train1, val1, test1 = stratified_split(mock_data, random_state=123)
        train2, val2, test2 = stratified_split(mock_data, random_state=123)
        
        pd.testing.assert_frame_equal(train1.reset_index(drop=True), train2.reset_index(drop=True))
        pd.testing.assert_frame_equal(val1.reset_index(drop=True), val2.reset_index(drop=True))
        pd.testing.assert_frame_equal(test1.reset_index(drop=True), test2.reset_index(drop=True))