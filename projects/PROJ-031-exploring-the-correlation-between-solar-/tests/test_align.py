import unittest
import pandas as pd
from code.align import flag_recurrent_activity

class TestFlagRecurrentActivity(unittest.TestCase):

    def test_flag_recurrent_activity(self):
        # Create a sample DataFrame
        data = {'event_time': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
                'recovery_time': pd.to_datetime(['2023-01-02', '2023-01-03', '2023-01-04']) }

        df = pd.DataFrame(data)
        df['is_recurrent'] = False # initialize the is_recurrent column
        # Call the function to flag recurrent activity
        result_df = flag_recurrent_activity(df.copy())

        # Assert that the 'is_recurrent' column has been added and values are correct
        self.assertTrue('is_recurrent' in result_df.columns)
        self.assertEqual(result_df['is_recurrent'][1], True)
        self.assertEqual(result_df['is_recurrent'][2], False)

if __name__ == '__main__':
    unittest.main()