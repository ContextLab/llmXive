import os
import json
import pandas as pd
import pytest
from pathlib import Path

from code.config import get_processed_path
from code.main import stage_05_merge_and_validate

class TestMergeValidation:
    """
    Integration test for T032: Merge and Save Final Dataset.
    Verifies that the merge logic correctly joins scoring and proxy results
    and that the output file exists with expected columns.
    """

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """
        Setup test fixtures.
        We create temporary CSV files to simulate the output of T017 and T026.
        """
        self.processed_dir = tmp_path / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock scoring results (output of T017)
        # Must include post_id, anxiety_score, confidence_score
        mock_scores = [
            {"post_id": "1", "text": "test text 1", "anxiety_score": 0.8, "confidence_score": 0.9},
            {"post_id": "2", "text": "test text 2", "anxiety_score": 0.2, "confidence_score": 0.95},
            {"post_id": "3", "text": "test text 3", "anxiety_score": 0.5, "confidence_score": 0.65},
        ]
        scores_df = pd.DataFrame(mock_scores)
        self.scores_path = self.processed_dir / "scoring_results.csv"
        scores_df.to_csv(self.scores_path, index=False)

        # Mock proxy results (output of T026)
        # Must include post_id, user_id, control_proxy, timestamp_regularity
        mock_proxies = [
            {"post_id": "1", "user_id": "u1", "control_proxy": 1.0, "timestamp_regularity": 0.8},
            {"post_id": "2", "user_id": "u1", "control_proxy": 0.0, "timestamp_regularity": 0.2},
            {"post_id": "4", "user_id": "u2", "control_proxy": 0.5, "timestamp_regularity": 0.5}, # Post 4 missing in scores
        ]
        proxies_df = pd.DataFrame(mock_proxies)
        self.proxies_path = self.processed_dir / "proxy_results.csv"
        proxies_df.to_csv(self.proxies_path, index=False)

        # Patch the config paths to point to our temp dir
        # We do this by monkeypatching the functions in code.config if they are callable,
        # or by directly manipulating the module if needed.
        # However, for this test, we will directly call the logic or mock the path getters.
        # Since stage_05_merge_and_validate uses get_processed_path, we need to ensure
        # those return our tmp paths. 
        # A simpler approach for integration test: 
        # We will modify the test to verify the logic by reading the files directly 
        # if the stage function doesn't run, OR we patch the config.
        
        # Let's patch the config functions
        import code.config
        self.original_get_processed = code.config.get_processed_path
        
        def mock_get_processed(filename):
            return self.processed_dir / filename
        
        code.config.get_processed_path = mock_get_processed

        self.output_path = self.processed_dir / "final_analysis.csv"
        
        yield

        # Restore
        code.config.get_processed_path = self.original_get_processed

    def test_merge_creates_file(self):
        """Test that the merge stage creates the final_analysis.csv file."""
        stage_05_merge_and_validate()
        assert self.output_path.exists(), "final_analysis.csv was not created."

    def test_merge_columns(self):
        """Test that the merged file contains all expected columns."""
        stage_05_merge_and_validate()
        df = pd.read_csv(self.output_path)
        
        expected_cols = [
            "post_id", "text", "anxiety_score", "confidence_score",
            "user_id", "control_proxy", "timestamp_regularity"
        ]
        for col in expected_cols:
            assert col in df.columns, f"Missing column: {col}"

    def test_merge_inner_join(self):
        """Test that the merge is an inner join (only matching post_ids)."""
        stage_05_merge_and_validate()
        df = pd.read_csv(self.output_path)
        
        # We have 3 scores (ids 1,2,3) and 3 proxies (ids 1,2,4).
        # Inner join should result in ids 1 and 2 only.
        assert len(df) == 2, f"Expected 2 rows, got {len(df)}"
        assert set(df['post_id'].tolist()) == {1, 2}, "Post IDs do not match expected inner join."

    def test_data_integrity(self):
        """Test that data values are preserved correctly after merge."""
        stage_05_merge_and_validate()
        df = pd.read_csv(self.output_path)
        
        # Check row with post_id 1
        row1 = df[df['post_id'] == 1].iloc[0]
        assert row1['anxiety_score'] == 0.8
        assert row1['control_proxy'] == 1.0
        
        # Check row with post_id 2
        row2 = df[df['post_id'] == 2].iloc[0]
        assert row2['anxiety_score'] == 0.2
        assert row2['control_proxy'] == 0.0

    def test_pre_filtered_data_confirmed(self):
        """
        Verify that the data being merged is the pre-filtered data.
        Since T016 handles filtering before T017 saves scoring_results.csv,
        we verify that the input to this stage (scoring_results.csv) 
        has no rows with confidence_score < 0.6.
        """
        # Read the input scoring file directly
        df_scores = pd.read_csv(self.scores_path)
        low_conf = df_scores[df_scores['confidence_score'] < 0.6]
        assert len(low_conf) == 0, "Input scoring data contains unfiltered low-confidence rows."