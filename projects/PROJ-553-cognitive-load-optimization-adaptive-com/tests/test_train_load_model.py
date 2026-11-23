import unittest
import pandas as pd
from code.train_load_model import log_transform_latency, aggregate_interaction_counts, engineer_features
import numpy as np

class TestTrainLoadModel(unittest.TestCase):

    def test_log_transform_latency(self):
        data = {'latency': [1, 2, 3]}
        df = pd.DataFrame(data)
        transformed_df = log_transform_latency(df.copy())
        self.assertTrue(np.allclose(np.exp(transformed_df['latency']) - 1, df['latency']))

    def test_aggregate_interaction_counts(self):
        data = {'session_id': [1, 1, 2, 2], 'error_flag': [0, 1, 0, 1], 'hint_request': [1, 0, 0, 1], 'pause': [0, 1, 1, 0]}
        df = pd.DataFrame(data)
        aggregated_df = aggregate_interaction_counts(df.copy())

        expected_data = {'session_id': [1, 2], 'error_flag': [1, 1], 'hint_request': [1, 1], 'pause': [1, 1]}
        expected_df = pd.DataFrame(expected_data)

        pd.testing.assert_frame_equal(aggregated_df[['session_id', 'error_flag', 'hint_request', 'pause']], expected_df)

    def test_engineer_features(self):
      data = {'latency': [1, 2, 3], 'error_flag': [0, 1, 0], 'hint_request': [1, 0, 0], 'pause':[0,1,1]}
      df = pd.DataFrame(data)

      engineered_df = engineer_features(df.copy())
      self.assertTrue('latency' in engineered_df.columns)
      self.assertTrue('error_flag' in engineered_df.columns)
      self.assertTrue('hint_request' in engineered_df.columns)
      self.assertTrue('pause' in engineered_df.columns)

if __name__ == '__main__':
    unittest.main()