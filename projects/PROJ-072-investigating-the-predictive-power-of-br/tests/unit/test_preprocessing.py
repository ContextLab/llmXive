import unittest
from code.preprocessing.metadata import load_exclusion_log, load_subject_status
import os
from pathlib import Path

class TestPreprocessingMetadata(unittest.TestCase):

    def test_load_exclusion_log(self):
        # Create a dummy exclusion log file
        log_path = "test_exclusion.log"
        with open(log_path, "w") as f:
            f.write("Subject 1 excluded due to motion\n")
            f.write("Subject 2 excluded due to artifact\n")

        exclusions = load_exclusion_log(log_path)
        self.assertEqual(len(exclusions), 2)
        self.assertIn("Subject 1 excluded due to motion", exclusions)

        # Clean up the dummy file
        os.remove(log_path)

    def test_load_subject_status(self):
        # Create a dummy subject status CSV file
        status_path = "test_subject_status.csv"
        with open(status_path, "w", newline="") as csvfile:
            csvfile.write("SubjectID,Status\n")
            csvfile.write("sub-01,Healthy\n")
            csvfile.write("sub-02,Patient\n")

        df = load_subject_status(status_path)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["SubjectID"], "sub-01")

        # Clean up the dummy file
        os.remove(status_path)
