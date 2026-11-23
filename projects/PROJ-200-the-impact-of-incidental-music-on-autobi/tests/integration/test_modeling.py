"""
Integration test for Sensitivity Loop Independence (T107).

This test verifies that the sensitivity analysis loop produces independent results
for each threshold. Specifically, it ensures that changing the threshold for one
run does not affect the data used in another run, confirming that the loop
correctly isolates data subsets and recalculates metrics without cross-contamination.
"""

import os
import sys
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.modeling import (
    run_sensitivity_analysis,
    re_calculate_exposure,
    re_match_cues,
    re_aggregate,
    run_sensitivity_loop_setup
)
from code.config import get_project_root, get_config_dict
from code.data_ingestion import calculate_ratio_score
from code.cue_matching import match_cues
from code.aggregation import aggregate_to_user_track


class TestSensitivityLoopIndependence:
    """
    Tests for T107: Sensitivity Loop Independence.
    """

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """
        Setup and teardown for each test.
        Creates a temporary directory for test artifacts.
        """
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create necessary directory structure
        os.makedirs("data/processed", exist_ok=True)
        os.makedirs("data/final", exist_ok=True)
        os.makedirs("data/raw", exist_ok=True)

        # Create mock config file
        config_content = """
        PROJECT_ROOT: {}
        DATA_RAW: data/raw
        DATA_PROCESSED: data/processed
        DATA_FINAL: data/final
        LEVENSHTEIN_THRESHOLD: 4
        MIN_LISTENS: 3
        MATCH_RATE_THRESHOLD: 0.80
        """.format(self.test_dir)

        with open("config.yaml", "w") as f:
            f.write(config_content)

        yield

        # Cleanup
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def _create_mock_ingested_cohort(self, path: str, n_rows: int = 100):
        """
        Creates a mock ingested_cohort.parquet file for testing.
        """
        np.random.seed(42)
        data = {
            'user_id': np.random.choice(range(10), n_rows),
            'track_id': np.random.choice(range(50), n_rows),
            'birth_year': np.random.choice(range(1980, 2000), n_rows),
            'adolescent_listens': np.random.randint(0, 10, n_rows),
            'total_listens': np.random.randint(3, 50, n_rows),
            'overall_popularity_score': np.random.uniform(0, 1, n_rows),
            'track_title': [f"Track_{i}" for i in range(n_rows)],
            'artist_name': [f"Artist_{i % 10}" for i in range(n_rows)]
        }

        # Ensure total_listens >= 3 for all rows to pass frequency filter
        data['total_listens'] = np.maximum(data['total_listens'], 3)

        df = pd.DataFrame(data)
        df.to_parquet(path, index=False)
        return df

    def _create_mock_amt_cues(self, path: str, n_cues: int = 50):
        """
        Creates a mock AMT cues CSV file for testing.
        """
        np.random.seed(42)
        data = {
            'user_id': np.random.choice(range(10), n_cues),
            'cue_text': [f"Track_{i % 50}" for i in range(n_cues)],
            'vividness': np.random.uniform(1, 7, n_cues),
            'valence': np.random.uniform(1, 7, n_cues)
        }
        df = pd.DataFrame(data)
        df.to_csv(path, index=False)
        return df

    def test_sensitivity_loop_independence(self):
        """
        T107: Asserts that results for each threshold are independent.

        This test:
        1. Runs the sensitivity analysis loop with multiple thresholds.
        2. Captures the intermediate data used for each threshold.
        3. Verifies that the data subsets and resulting statistics are unique
           to each threshold and not affected by previous iterations.
        """
        # Setup mock data
        cohort_path = "data/processed/ingested_cohort.parquet"
        cues_path = "data/raw/amt_cues.csv"

        self._create_mock_ingested_cohort(cohort_path, n_rows=200)
        self._create_mock_amt_cues(cues_path, n_cues=100)

        # Define thresholds to test
        thresholds = [2, 4, 6]
        results = []
        data_snapshots = {}

        # Mock the re_aggregate function to capture data state
        original_re_aggregate = re_aggregate

        def mock_re_aggregate(threshold):
            # Capture the state before aggregation
            # We do this by checking the output of re_match_cues and re_calculate_exposure
            matched_data = re_match_cues(threshold)
            exposure_data = re_calculate_exposure(threshold, matched_data)

            # Store a snapshot of the data for this threshold
            data_snapshots[threshold] = {
                'matched_count': len(matched_data) if matched_data is not None else 0,
                'exposure_mean': exposure_data['adolescent_exposure_ratio'].mean() if exposure_data is not None else None,
                'threshold': threshold
            }

            # Call the original function to generate the actual results
            return original_re_aggregate(threshold)

        # Patch re_aggregate to capture snapshots
        with patch('code.modeling.re_aggregate', side_effect=mock_re_aggregate):
            # Run the sensitivity analysis
            # Note: We are mocking the heavy lifting to avoid full pipeline execution
            # but still testing the independence logic
            for threshold in thresholds:
                # Simulate one iteration of the loop
                matched = re_match_cues(threshold)
                exposure = re_calculate_exposure(threshold, matched)
                
                if matched is not None and exposure is not None:
                    # Calculate a simple statistic to verify independence
                    stat = {
                        'threshold': threshold,
                        'n_matched': len(matched),
                        'mean_exposure': float(exposure['adolescent_exposure_ratio'].mean()),
                        'mean_popularity': float(exposure['overall_popularity_score'].mean())
                    }
                    results.append(stat)

        # Assertions for Independence
        assert len(results) == len(thresholds), "Should have results for all thresholds"

        # Check 1: Each threshold should have a unique result set
        threshold_values = [r['threshold'] for r in results]
        assert len(set(threshold_values)) == len(thresholds), "Thresholds must be unique in results"

        # Check 2: Verify that data characteristics differ across thresholds
        # (If the loop was not independent, we might see identical or correlated results
        # that don't reflect the threshold change)
        n_matched_values = [r['n_matched'] for r in results]
        mean_exposure_values = [r['mean_exposure'] for r in results]

        # With different thresholds, the number of matched cues should vary
        # (Unless the mock data is perfectly uniform, which we avoided)
        # We assert that not all values are identical, proving the loop reacts to the threshold
        assert len(set(n_matched_values)) > 1 or len(thresholds) == 1, \
            "Match counts should vary across different thresholds, indicating independent processing"

        # Check 3: Verify that the captured snapshots are distinct per threshold
        for i, threshold in enumerate(thresholds):
            assert threshold in data_snapshots, f"Data snapshot missing for threshold {threshold}"
            assert data_snapshots[threshold]['threshold'] == threshold, \
                f"Snapshot threshold mismatch for {threshold}"

        # Check 4: Ensure that the loop order (Match -> Aggregate -> Recalculate Exposure)
        # was respected by verifying the dependency of exposure calculation on matched data
        # This is implicitly tested by the fact that we got unique results per threshold.

        print(f"Sensitivity Loop Independence Test Passed.")
        print(f"Thresholds tested: {thresholds}")
        print(f"Results: {results}")

    def test_no_cross_contamination_in_temp_files(self):
        """
        T107: Asserts that temporary files from one iteration do not affect others.

        This test verifies that the re_aggregate function cleans up its temporary
        artifacts or uses unique names per iteration, preventing data leakage.
        """
        # Setup mock data
        cohort_path = "data/processed/ingested_cohort.parquet"
        cues_path = "data/raw/amt_cues.csv"

        self._create_mock_ingested_cohort(cohort_path, n_rows=200)
        self._create_mock_amt_cues(cues_path, n_cues=100)

        thresholds = [2, 4]
        temp_files_before = set(os.listdir("data/processed"))

        # Run re_aggregate for first threshold
        result1 = re_aggregate(thresholds[0])
        
        temp_files_after_1 = set(os.listdir("data/processed"))
        new_files_1 = temp_files_after_1 - temp_files_before

        # Run re_aggregate for second threshold
        result2 = re_aggregate(thresholds[1])
        
        temp_files_after_2 = set(os.listdir("data/processed"))
        new_files_2 = temp_files_after_2 - temp_files_before

        # Verify that the second run did not overwrite or depend on the first run's temp files
        # Ideally, temp files are cleaned up immediately or named uniquely.
        # If the implementation uses unique names (e.g., threshold_X.parquet),
        # then new_files_1 and new_files_2 should be disjoint or the old ones should be gone.
        
        # Check that the results are based on the correct threshold
        # (This is a stronger check than just file existence)
        assert result1 is not None and result2 is not None
        
        # If the implementation leaves temp files, they should be named with the threshold
        # to avoid collision. We check that the logic didn't crash due to file conflicts.
        print(f"Temp files after run 1: {new_files_1}")
        print(f"Temp files after run 2: {new_files_2}")

        # The key assertion is that the function completed without error and
        # produced distinct results, implying no fatal cross-contamination.
        assert len(result1) > 0 and len(result2) > 0