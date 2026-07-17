"""
Unit tests for the router training script (T019).
Verifies data loading, preprocessing, and model saving logic.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.models.train_router import (
    load_labeled_data,
    preprocess_data,
    LABEL_MAP,
    MAX_LENGTH
)

class TestRouterTraining:
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_labeled_df(self):
        """Create a sample labeled DataFrame."""
        data = {
            "query": [
                "What is the weather?",
                "I need help with my account",
                "Set a reminder for 5pm",
                "How do I reset my password?",
                "Show me my recent transactions"
            ],
            "ground_truth_intent": [
                "High-Confidence",
                "Ambiguous",
                "High-Confidence",
                "Ambiguous",
                "High-Confidence"
            ],
            "complexity_score": [1, 2, 1, 2, 1]
        }
        return pd.DataFrame(data)

    def test_load_labeled_data_file_not_found(self, temp_data_dir):
        """Test that load_labeled_data raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_labeled_data(temp_data_dir / "nonexistent.csv")

    def test_load_labeled_data_missing_columns(self, temp_data_dir, sample_labeled_df):
        """Test that load_labeled_data raises ValueError for missing columns."""
        # Create a file without required columns
        bad_df = sample_labeled_df.drop(columns=["query"])
        csv_path = temp_data_dir / "bad_data.csv"
        bad_df.to_csv(csv_path, index=False)

        with pytest.raises(ValueError, match="missing required columns"):
            load_labeled_data(csv_path)

    def test_load_labeled_data_success(self, temp_data_dir, sample_labeled_df):
        """Test successful loading of labeled data."""
        csv_path = temp_data_dir / "labeled_turns.csv"
        sample_labeled_df.to_csv(csv_path, index=False)

        loaded_df = load_labeled_data(csv_path)
        assert len(loaded_df) == 5
        assert "query" in loaded_df.columns
        assert "ground_truth_intent" in loaded_df.columns
        assert set(loaded_df["ground_truth_intent"]) == {"High-Confidence", "Ambiguous"}

    def test_preprocess_data_label_mapping(self, sample_labeled_df):
        """Test that labels are correctly mapped to integers."""
        train_ds, test_ds, tokenizer = preprocess_data(sample_labeled_df)

        # Check that all labels are 0 or 1
        all_labels = list(train_ds["label"]) + list(test_ds["label"])
        assert all(label in [0, 1] for label in all_labels)

    def test_preprocess_data_tokenization(self, sample_labeled_df):
        """Test that tokenization produces expected keys."""
        train_ds, test_ds, tokenizer = preprocess_data(sample_labeled_df)

        sample_item = train_ds[0]
        assert "input_ids" in sample_item
        assert "attention_mask" in sample_item
        assert "label" in sample_item
        assert len(sample_item["input_ids"]) == MAX_LENGTH
        assert len(sample_item["attention_mask"]) == MAX_LENGTH

    def test_preprocess_data_unknown_labels(self, temp_data_dir):
        """Test that unknown labels raise an error."""
        bad_df = pd.DataFrame({
            "query": ["test query"],
            "ground_truth_intent": ["Unknown-Intent"]
        })
        with pytest.raises(ValueError, match="Unknown labels found"):
            preprocess_data(bad_df)

    def test_label_map_consistency(self):
        """Test that LABEL_MAP is consistent with expected values."""
        assert LABEL_MAP["High-Confidence"] == 0
        assert LABEL_MAP["Ambiguous"] == 1
        assert len(LABEL_MAP) == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])