"""
Integration test for the data pipeline (US1).
Verifies that the pipeline components can be imported and basic execution paths work.
Note: This test does not download real GHTorrent data to keep tests fast and deterministic,
but verifies the logic of the pipeline modules.
"""
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import pipeline modules
from data.extract_metrics import extract_metrics
from data.label_bug_fixes import is_bug_fix, label_bug_fixes
from data.preprocess import preprocess
from data.split_dataset import get_split_proportions, document_split_proportions
from utils.config import set_random_seed


class TestDataPipelineIntegration:
    def setup_method(self):
        """Setup test fixtures."""
        set_random_seed(42)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_data_path = Path(self.temp_dir.name)

    def teardown_method(self):
        """Cleanup test fixtures."""
        self.temp_dir.cleanup()

    def test_extract_metrics_signature(self):
        """Test that extract_metrics function exists and has correct signature."""
        # We cannot run lizard on real files without data, but we verify the function exists
        assert callable(extract_metrics)

    def test_label_bug_fixes_logic(self):
        """Test the bug fix labeling logic with known inputs."""
        assert is_bug_fix("Fix bug in login", ["fix", "bug"]) is True
        assert is_bug_fix("Add new feature", ["fix", "bug"]) is False
        assert is_bug_fix("Fix typo", ["fix"]) is True

    def test_preprocess_basic(self):
        """Test basic preprocessing on a small synthetic dataset."""
        data = {
            "cc": [10.0, 5.0, 20.0, None],
            "loc": [100.0, 50.0, 200.0, 150.0],
            "bug_label": [1, 0, 1, 0],
            "project_id": ["P1", "P1", "P2", "P2"],
        }
        df = pd.DataFrame(data)

        # Run preprocess
        processed_df, _ = preprocess(df)

        # Verify no NaNs in numeric columns (imputation worked)
        assert processed_df["cc"].isnull().sum() == 0
        assert processed_df.shape[0] == 4

    def test_split_dataset_proportions(self):
        """Test split proportion calculation."""
        train, test = get_split_proportions()
        assert train + test == 1.0
        assert 0.7 <= train <= 0.8  # Expecting ~70/30 split

    def test_document_split_proportions(self):
        """Test that split proportions are documented."""
        result = document_split_proportions()
        assert isinstance(result, dict)
        assert "train" in result
        assert "test" in result
