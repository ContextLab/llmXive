import unittest
import pandas as pd
from code.data.preprocess import write_processed_data
from code.utils.update_state import load_state_file
import os

class TestWriteProcessedData(unittest.TestCase):

    def setUp(self):
        self.output_path = "data/processed/test_molecules_processed.csv"
        self.state_file_path = "state/projects/test_state.yaml"
        # Create a dummy state file
        with open(self.state_file_path, "w") as f:
            f.write("""
            artifacts: {}
            """)

        self.data = {'SMILES': ['CCO', 'CC(=O)O'], 'experimental_value': [1.0, 2.0], 'tpsa': [40.0, 60.0]}
        self.df = pd.DataFrame(self.data)

    def tearDown(self):
        # Clean up the created files
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        if os.path.exists(self.state_file_path):
            os.remove(self.state_file_path)

    def test_write_processed_data_creates_file(self):
        write_processed_data(self.df, self.output_path, self.state_file_path)
        self.assertTrue(os.path.exists(self.output_path))

    def test_write_processed_data_updates_state_file(self):
        write_processed_data(self.df, self.output_path, self.state_file_path)
        state = load_state_file(self.state_file_path)
        self.assertIn(self.output_path, state["artifacts"])
        self.assertIsNotNone(state["artifacts"][self.output_path])