import unittest
import pandas as pd
import os
import tempfile
import json
from code.evaluator import stratified_split, run_stratified_split, load_metrics

class TestEvaluator(unittest.TestCase):

    def test_stratified_split_preserves_label_ratio_in_metrics_csv(self):
        # Create a sample DataFrame
        data = {'metric': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
                'label': ['success', 'failure', 'success', 'failure', 'success', 'failure']}
        df = pd.DataFrame(data)

        # Split the DataFrame
        train_df, test_df = stratified_split(df, label_column='label', test_size=0.33, random_state=42)

        # Check if the label ratios are preserved in train and test sets
        train_success_ratio = len(train_df[train_df['label'] == 'success']) / len(train_df)
        test_success_ratio = len(test_df[test_df['label'] == 'success']) / len(test_df)
        original_success_ratio = len(df[df['label'] == 'success']) / len(df)

        self.assertAlmostEqual(train_success_ratio, original_success_ratio, places=1)
        self.assertAlmostEqual(test_success_ratio, original_success_ratio, places=1)

    def test_run_stratified_split_writes_files(self):
        """Test that run_stratified_split actually writes the CSV files to disk."""
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = os.path.join(tmpdir, "metrics.csv")
            train_file = os.path.join(tmpdir, "train_metrics.csv")
            test_file = os.path.join(tmpdir, "test_metrics.csv")
            
            # Create input data
            data = {'trajectory_id': ['t1', 't2', 't3', 't4', 't5', 't6'],
                    'global_connectivity': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
                    'avg_branching_factor': [1.0, 2.0, 1.5, 2.5, 1.2, 2.2],
                    'label': ['success', 'failure', 'success', 'failure', 'success', 'failure']}
            df = pd.DataFrame(data)
            df.to_csv(input_file, index=False)
            
            # Run the function
            run_stratified_split(input_file, train_file, test_file, label_column='label', test_size=0.33, random_state=42)
            
            # Verify files exist
            self.assertTrue(os.path.exists(train_file), "train_metrics.csv was not created")
            self.assertTrue(os.path.exists(test_file), "test_metrics.csv was not created")
            
            # Verify content
            train_df = load_metrics(train_file)
            test_df = load_metrics(test_file)
            
            # Check row counts (approximate for small sample)
            self.assertEqual(len(train_df) + len(test_df), len(df), "Total rows mismatch")
            
            # Verify label distribution tolerance (5%)
            original_success_ratio = len(df[df['label'] == 'success']) / len(df)
            train_success_ratio = len(train_df[train_df['label'] == 'success']) / len(train_df)
            test_success_ratio = len(test_df[test_df['label'] == 'success']) / len(test_df)
            
            # Allow 5% tolerance as per task description
            self.assertAlmostEqual(train_success_ratio, original_success_ratio, places=1, msg="Train split label ratio deviates > 10%")
            self.assertAlmostEqual(test_success_ratio, original_success_ratio, places=1, msg="Test split label ratio deviates > 10%")

    def test_run_stratified_split_missing_input(self):
        """Test that run_stratified_split fails gracefully if input file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = os.path.join(tmpdir, "nonexistent.csv")
            train_file = os.path.join(tmpdir, "train.csv")
            test_file = os.path.join(tmpdir, "test.csv")
            
            # Should raise an error or handle missing file
            with self.assertRaises(FileNotFoundError):
                # We expect pd.read_csv to raise if file doesn't exist
                # run_stratified_split calls load_metrics which calls pd.read_csv
                run_stratified_split(input_file, train_file, test_file)