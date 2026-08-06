import unittest
import pandas as pd
from code.evaluator import stratified_split

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