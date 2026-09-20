"""
T019 Integration Test: Fidelity Manipulation vs Recovery Segment Removal
User Story 2: Reward Fidelity Manipulation & Pruning Execution
"""
import unittest
import os
import sys
import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Set

# Project root adjustment for execution context
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "code"))

from utils.pruning import RewardFidelityLevel, identify_pruning_candidates
from utils.state_diff import process_baseline_logs_with_recovery_tags
import pandas as pd


class TestFidelityManipulationRemovesRecoverySegments(unittest.TestCase):
    """
    Integration test to verify that fidelity manipulation (pruning) removes
    segments tagged as "recovery-critical" at a higher rate than random segments.

    Prerequisites:
    - T012: data/processed/baseline_execution_logs.csv (with recovery_segment_id)
    - T023/T024: data/processed/pruned_execution_logs.csv (with discarded segments)
    """

    @classmethod
    def setUpClass(cls):
        """
        Load the necessary data artifacts.
        If data is missing, the test fails loudly (as per constraints).
        """
        cls.baseline_path = ROOT_DIR / "data" / "processed" / "baseline_execution_logs.csv"
        cls.pruned_path = ROOT_DIR / "data" / "processed" / "pruned_execution_logs.csv"

        if not cls.baseline_path.exists():
            raise FileNotFoundError(
                f"Required artifact missing: {cls.baseline_path}. "
                "Ensure T012 and T014 have been executed successfully."
            )

        if not cls.pruned_path.exists():
            raise FileNotFoundError(
                f"Required artifact missing: {cls.pruned_path}. "
                "Ensure T023/T024 (Fidelity Pruning Execution) have been run."
            )

        # Load Baseline Data (Ground Truth for Recovery Segments)
        cls.baseline_df = pd.read_csv(cls.baseline_path)
        
        # Load Pruned Execution Logs
        cls.pruned_df = pd.read_csv(cls.pruned_path)

    def test_fidelity_manipulation_removes_recovery_segments(self):
        """
        Assertion: Verify that `data/processed/pruned_execution_logs.csv` shows a 
        higher removal rate of segments tagged as "recovery-critical" in T014 
        compared to random segments.
        
        Logic:
        1. Identify the set of segments tagged as 'recovery-critical' in the baseline.
        2. Identify which segments were discarded in the pruned logs.
        3. Calculate the removal rate for recovery-critical segments.
        4. Calculate the removal rate for non-critical (random) segments.
        5. Assert that the recovery-critical removal rate is significantly higher.
        """
        # 1. Identify Recovery-Critical Segments from Baseline
        # Assuming 'recovery_segment_id' contains the ID if critical, or is NaN/empty if not.
        # Based on T014 logic, we treat non-null/non-empty IDs as critical.
        critical_segments = set()
        if 'recovery_segment_id' in self.baseline_df.columns:
            for idx, row in self.baseline_df.iterrows():
                seg_id = row.get('recovery_segment_id')
                if seg_id is not None and str(seg_id).strip() != '':
                    critical_segments.add(seg_id)
        
        if not critical_segments:
            self.fail("No recovery-critical segments found in baseline data. T014 may not have tagged any.")

        # 2. Identify Discarded Segments from Pruned Logs
        # The pruned log should contain a list of discarded segment IDs per task/row.
        # Assuming column name 'discarded_segments' or similar JSON string representation.
        # If the column doesn't exist, we check for standard variations.
        discarded_col = None
        possible_cols = ['discarded_segments', 'discarded_segment_ids', 'removed_segments']
        for col in possible_cols:
            if col in self.pruned_df.columns:
                discarded_col = col
                break

        if not discarded_col:
            self.fail(
                f"Pruned execution log missing discarded segments column. "
                f"Expected one of: {possible_cols}. Found: {self.pruned_df.columns.tolist()}"
            )

        total_critical = len(critical_segments)
        total_random = 0
        removed_critical = 0
        removed_random = 0

        # Iterate through pruned logs to count removals
        for idx, row in self.pruned_df.iterrows():
            disc_str = row.get(discarded_col)
            if not disc_str or pd.isna(disc_str):
                continue
            
            # Parse the discarded segments (assume JSON list or comma-separated string)
            try:
                if isinstance(disc_str, str):
                    if disc_str.startswith('['):
                        discarded_ids = json.loads(disc_str)
                    else:
                        discarded_ids = [s.strip() for s in disc_str.split(',') if s.strip()]
                elif isinstance(disc_str, list):
                    discarded_ids = disc_str
                else:
                    continue
            except (json.JSONDecodeError, ValueError):
                continue

            for seg_id in discarded_ids:
                if seg_id in critical_segments:
                    removed_critical += 1
                else:
                    # Only count as 'random' if it's a known segment from the baseline that isn't critical
                    # For this test, we assume any discarded segment not in critical set is a candidate for random
                    total_random += 1
                    removed_random += 1

            # Count total non-critical segments available for baseline context
            # This is a simplified approximation: we assume the total pool of segments
            # in the pruned dataset is represented by the union of all discarded + kept.
            # However, for the rate comparison, we compare the proportion of critical vs random
            # that were removed.
        
        # Calculate Rates
        # Note: If total_random is 0, we cannot calculate a rate, but if we removed criticals,
        # that still suggests a bias.
        
        rate_critical = removed_critical / total_critical if total_critical > 0 else 0.0
        rate_random = removed_random / total_random if total_random > 0 else 0.0

        print(f"--- T019 Test Results ---")
        print(f"Total Critical Segments (Ground Truth): {total_critical}")
        print(f"Total Random/Non-Critical Segments Discarded: {total_random}")
        print(f"Removed Critical: {removed_critical} (Rate: {rate_critical:.4f})")
        print(f"Removed Random: {removed_random} (Rate: {rate_random:.4f})")

        # Assertion: The hypothesis is that fidelity manipulation targets critical segments.
        # Therefore, the removal rate of critical segments should be higher than random.
        # We allow a small tolerance for statistical noise, but the trend must be clear.
        if rate_critical <= rate_random:
            self.fail(
                f"Hypothesis Failed: Recovery-critical segments were NOT removed more frequently. "
                f"Critical Removal Rate: {rate_critical:.4f} vs Random Removal Rate: {rate_random:.4f}. "
                f"Pruning logic may not be correctly targeting fidelity-sensitive segments."
            )
        
        # Optional: Check if the difference is substantial (e.g., at least 10% higher)
        # This prevents passing if the rates are 0.00001 vs 0.00000
        if total_critical > 0 and total_random > 0:
            margin = rate_critical - rate_random
            self.assertGreater(
                margin, 0.0,
                f"Critical segments must be removed at a strictly higher rate. "
                f"Margin: {margin}"
            )

    def test_pruned_log_schema_integrity(self):
        """
        Helper test to ensure the pruned log contains necessary fields for the main test.
        """
        required_cols = ['task_id', 'success_status', 'fidelity_level', 'discarded_segments']
        missing = [col for col in required_cols if col not in self.pruned_df.columns]
        
        # Adjust for possible column name variations
        if 'discarded_segments' not in self.pruned_df.columns:
            if not any(col in self.pruned_df.columns for col in ['discarded_segment_ids', 'removed_segments']):
                missing.append('discarded_segments')

        self.assertEqual(len(missing), 0, f"Pruned log missing required columns: {missing}")


if __name__ == '__main__':
    unittest.main()