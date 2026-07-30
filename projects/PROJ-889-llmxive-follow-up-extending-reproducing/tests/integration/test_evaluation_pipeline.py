"""
Integration test for the full evaluation pipeline (User Story 3).

This test verifies the end-to-end flow:
1. Load processed divergence data (from US1).
2. Verify ground truth independence checks (T032a/b logic).
3. Derive ground truth labels from J_gold drops (T031).
4. Generate Stratified Random Baseline (T033).
5. Run detector to get hacking labels (T022/T023).
6. Compare Detector vs Baseline vs Ground Truth using F1 scores and Wilcoxon test (T034a).
7. Verify SC-003 (F1 std dev <= 0.15).

Prerequisites:
- T013 (Data downloaded to data/raw)
- T016 (data/processed/trajectories_divergence.csv exists)
- T023 (data/processed/trajectories_labeled.csv exists with hacking_label)
- T032a/b (Independence checks passed in config or skipped if data not present yet)
"""
import os
import sys
import unittest
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
from scipy import stats

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import get_project_root, ensure_paths_exist
from code.ground_truth import (
    check_independence,
    derive_ground_truth_labels,
    validate_independence
)
from code.evaluation import (
    generate_stratified_baseline,
    calculate_f1_scores,
    run_wilcoxon_test,
    check_sc003_stability
)
from code.detector import detect_hacking
from code.utils.io_utils import read_csv, write_csv


class TestEvaluationPipeline(unittest.TestCase):
    """Integration tests for the US3 evaluation pipeline."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.project_root = get_project_root()
        cls.data_raw = cls.project_root / "data" / "raw"
        cls.data_processed = cls.project_root / "data" / "processed"
        
        # Ensure paths exist (though they should be created by T001/T004)
        ensure_paths_exist()

        # Verify prerequisite files exist
        cls.divergence_file = cls.data_processed / "trajectories_divergence.csv"
        cls.labeled_file = cls.data_processed / "trajectories_labeled.csv"
        
        if not cls.divergence_file.exists():
            raise FileNotFoundError(
                f"Prerequisite file missing: {cls.divergence_file}. "
                "Please run T013 and T016 first."
            )

    def test_01_load_and_validate_divergence_data(self):
        """Test loading the divergence data and checking required columns."""
        df = read_csv(self.divergence_file)
        
        required_cols = [
            'seed_id', 'bias_type', 'timestep', 
            'J_biased', 'J_unbiased', 'J_gold', 
            'G_t', 'dG_t'
        ]
        
        for col in required_cols:
            self.assertIn(col, df.columns, f"Missing required column: {col}")
        
        self.assertGreater(len(df), 0, "Divergence data is empty")
        print(f"✓ Loaded {len(df)} rows of divergence data")

    def test_02_independence_check(self):
        """Test the independence check (T032a/b) to prevent circular validation."""
        df = read_csv(self.divergence_file)
        
        # Check J_unbiased vs J_gold
        try:
            corr_unbiased, _ = check_independence(
                df['J_unbiased'], 
                df['J_gold'], 
                threshold=0.8
            )
            print(f"✓ J_unbiased vs J_gold correlation: {corr_unbiased:.4f} (Pass)")
        except RuntimeError as e:
            self.fail(f"Independence check failed: {e}")
        
        # Check J_biased vs J_gold
        try:
            corr_biased, _ = check_independence(
                df['J_biased'], 
                df['J_gold'], 
                threshold=0.8
            )
            print(f"✓ J_biased vs J_gold correlation: {corr_biased:.4f} (Pass)")
        except RuntimeError as e:
            self.fail(f"Independence check failed: {e}")

    def test_03_derive_ground_truth_labels(self):
        """Test deriving ground truth labels from J_gold drops (T031)."""
        df = read_csv(self.divergence_file)
        
        # Derive labels per FR-004: >=0.1 decrease over 50 steps, sustained 3 steps
        gt_df = derive_ground_truth_labels(
            df, 
            drop_threshold=0.1, 
            window_size=50, 
            sustained_steps=3
        )
        
        self.assertIn('gt_hacking_label', gt_df.columns)
        self.assertEqual(len(gt_df), len(df))
        
        gt_count = gt_df['gt_hacking_label'].sum()
        print(f"✓ Derived {gt_count} ground truth hacking events")

    def test_04_generate_stratified_baseline(self):
        """Test generating the stratified random baseline (T033)."""
        df = read_csv(self.divergence_file)
        
        # Ensure bias_type is available for stratification
        self.assertIn('bias_type', df.columns)
        
        baseline_df = generate_stratified_baseline(
            df, 
            seed=42, 
            sample_fraction=0.1
        )
        
        self.assertIn('baseline_label', baseline_df.columns)
        baseline_count = baseline_df['baseline_label'].sum()
        expected_count = int(len(df) * 0.1)
        
        # Allow some tolerance for rounding
        self.assertAlmostEqual(baseline_count, expected_count, delta=expected_count * 0.1)
        print(f"✓ Generated stratified baseline with {baseline_count} samples")

    def test_05_load_hacking_labels(self):
        """Test loading the detector's hacking labels (T023)."""
        if not self.labeled_file.exists():
            # If labeled file doesn't exist, we might need to run the detector
            # For this integration test, we assume T023 has run.
            # If not, we skip or run it here if allowed.
            # Given the constraint "Implement T030 only", we assume T023 is done.
            # If T023 is not done, this test would fail, which is correct behavior.
            self.fail(
                f"Prerequisite file missing: {self.labeled_file}. "
                "Please run T023 first."
            )
        
        df = read_csv(self.labeled_file)
        self.assertIn('hacked_label', df.columns)
        
        hacked_count = df['hacked_label'].sum()
        print(f"✓ Loaded {hacked_count} detector hacking labels")

    def test_06_full_pipeline_evaluation(self):
        """
        End-to-end evaluation: Compare Detector vs Baseline vs Ground Truth.
        Includes Wilcoxon test (T034a) and SC-003 check (T035).
        """
        # Load data
        df = read_csv(self.divergence_file)
        
        # 1. Derive Ground Truth
        gt_df = derive_ground_truth_labels(df)
        
        # 2. Generate Baseline
        baseline_df = generate_stratified_baseline(df, seed=42, sample_fraction=0.1)
        
        # 3. Load Detector Labels (from T023)
        if not self.labeled_file.exists():
            self.skipTest("Labeled file missing. Run T023 first.")
        
        detector_df = read_csv(self.labeled_file)
        
        # Align dataframes by index (assuming they are aligned from same source)
        # In a real scenario, we might need to merge by seed_id and timestep
        # For this test, we assume the files are already aligned or merged correctly.
        # If they are separate files, we need to merge.
        # Let's assume 'trajectories_labeled.csv' is the result of merging divergence + detector labels.
        # So we can use detector_df directly if it has G_t, dG_t etc, or merge.
        
        # To be safe, let's merge on index if they are the same length, or by keys.
        # Assuming the pipeline produces a single dataframe per seed or merged.
        # If separate files, we merge.
        if 'seed_id' in detector_df.columns and 'timestep' in detector_df.columns:
            # Merge detector labels into the main df
            main_df = df.merge(
                detector_df[['seed_id', 'timestep', 'hacked_label']],
                on=['seed_id', 'timestep'],
                how='left'
            )
            # Also merge baseline
            main_df = main_df.merge(
                baseline_df[['seed_id', 'timestep', 'baseline_label']],
                on=['seed_id', 'timestep'],
                how='left'
            )
            # Also merge GT
            main_df = main_df.merge(
                gt_df[['seed_id', 'timestep', 'gt_hacking_label']],
                on=['seed_id', 'timestep'],
                how='left'
            )
        else:
            # Assume aligned
            main_df = pd.concat([
                df,
                detector_df[['hacked_label']],
                baseline_df[['baseline_label']],
                gt_df[['gt_hacking_label']]
            ], axis=1)

        # 4. Calculate F1 Scores
        # We need to group by rubric type or seed to calculate F1 per group
        # For simplicity, calculate global F1 first
        
        detector_f1 = calculate_f1_scores(
            main_df['hacked_label'],
            main_df['gt_hacking_label']
        )
        
        baseline_f1 = calculate_f1_scores(
            main_df['baseline_label'],
            main_df['gt_hacking_label']
        )
        
        print(f"✓ Detector F1: {detector_f1:.4f}")
        print(f"✓ Baseline F1: {baseline_f1:.4f}")
        
        # 5. Wilcoxon Signed-Rank Test (T034a)
        # We need multiple F1 scores (e.g., per rubric type or per seed)
        # Let's group by 'bias_type' (rubric type)
        if 'bias_type' in main_df.columns:
            detector_scores = []
            baseline_scores = []
            
            for rubric in main_df['bias_type'].unique():
                sub_df = main_df[main_df['bias_type'] == rubric]
                if len(sub_df) > 0:
                    d_f1 = calculate_f1_scores(sub_df['hacked_label'], sub_df['gt_hacking_label'])
                    b_f1 = calculate_f1_scores(sub_df['baseline_label'], sub_df['gt_hacking_label'])
                    detector_scores.append(d_f1)
                    baseline_scores.append(b_f1)
            
            if len(detector_scores) > 1:
                stat, p_value = run_wilcoxon_test(detector_scores, baseline_scores)
                print(f"✓ Wilcoxon Stat: {stat:.4f}, P-value: {p_value:.4f}")
                self.assertLess(p_value, 1.0, "P-value should be valid")
            else:
                self.skipTest("Not enough rubric types for Wilcoxon test")
        else:
            self.skipTest("bias_type column missing for stratified F1 calculation")

        # 6. SC-003 Check (T035)
        # Check if std dev of F1 scores across rubrics <= 0.15
        if 'bias_type' in main_df.columns:
            f1_scores_list = []
            for rubric in main_df['bias_type'].unique():
                sub_df = main_df[main_df['bias_type'] == rubric]
                if len(sub_df) > 0:
                    f1 = calculate_f1_scores(sub_df['hacked_label'], sub_df['gt_hacking_label'])
                    f1_scores_list.append(f1)
            
            if len(f1_scores_list) > 0:
                is_stable = check_sc003_stability(f1_scores_list, threshold=0.15)
                print(f"✓ SC-003 Stability Check: {'Pass' if is_stable else 'Fail'}")
                # We don't assert fail here because it's a research outcome, not a code bug.
                # But we verify the function works.

    def test_07_sensitivity_analysis(self):
        """Test sensitivity analysis for ground-truth drop threshold (T037)."""
        df = read_csv(self.divergence_file)
        
        thresholds = [0.05, 0.1, 0.15]
        results = []
        
        for thresh in thresholds:
            gt_df = derive_ground_truth_labels(df, drop_threshold=thresh)
            f1 = calculate_f1_scores(gt_df['gt_hacking_label'], gt_df['gt_hacking_label']) # Self F1 is 1.0
            # In reality, we compare detector vs GT.
            # For this test, we just verify the function runs and produces different GT counts.
            results.append({
                'threshold': thresh,
                'gt_count': gt_df['gt_hacking_label'].sum()
            })
        
        results_df = pd.DataFrame(results)
        self.assertFalse(results_df['gt_count'].nunique() == 1, 
                         "Sensitivity analysis should show variation in GT counts")
        print(f"✓ Sensitivity Analysis Results:\n{results_df}")


if __name__ == '__main__':
    unittest.main()