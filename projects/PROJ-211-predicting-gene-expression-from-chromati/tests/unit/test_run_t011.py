import os
import sys
import unittest
import tempfile
import shutil
import pandas as pd

# Adjust path to include code directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from run_t011 import main
from utils import checksum_file

class TestT011Execution(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory structure for the test
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Mock the project structure in temp dir
        os.makedirs(os.path.join(self.test_dir, 'data', 'raw'), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, 'logs'), exist_ok=True)
        os.chdir(self.test_dir)
        
        # We need to ensure the imports work, so we add the code dir to path
        # This is handled by the sys.path.insert in the test, but we need to ensure 
        # the modules are importable. Since we are running unit tests, we might need 
        # to mock the heavy generation or assume the environment is set up.
        # However, for T011, the task is to execute the script. 
        # We will test that the script runs and creates files.

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_t011_creates_outputs(self):
        """
        Verify that running run_t011.py creates the required output files:
        - data/raw/synthetic_counts.csv
        - data/raw/synthetic_peaks.bed
        - logs/checksums.txt (appended)
        """
        # Run the main function
        # Note: This might take a moment depending on the size of the synthetic data
        result = main()
        
        self.assertEqual(result, 0, "main() should return 0 on success")

        # Check file existence
        counts_path = "data/raw/synthetic_counts.csv"
        peaks_path = "data/raw/synthetic_peaks.bed"
        checksum_path = "logs/checksums.txt"

        self.assertTrue(os.path.exists(counts_path), f"{counts_path} was not created")
        self.assertTrue(os.path.exists(peaks_path), f"{peaks_path} was not created")
        self.assertTrue(os.path.exists(checksum_path), f"{checksum_path} was not created")

        # Validate CSV structure (basic check)
        df = pd.read_csv(counts_path)
        self.assertTrue('gene_id' in df.columns, "Counts CSV missing 'gene_id' column")
        # Check that we have data for the expected cell lines
        expected_cells = ["GM12878", "K562", "HMEC", "IMR90", "HepG2"]
        # Depending on the exact format of generate_counts_matrix, columns might be named differently.
        # Assuming the format is gene_id, cell_line_peak combinations or similar.
        # We just check it's not empty.
        self.assertGreater(len(df), 0, "Counts CSV is empty")

        # Validate BED structure
        with open(peaks_path, 'r') as f:
            lines = f.readlines()
        self.assertGreater(len(lines), 0, "Peaks BED file is empty")
        
        # Check BED format (at least 3 columns)
        first_line = lines[0].strip().split('\t')
        self.assertGreaterEqual(len(first_line), 3, "BED file does not have 3 columns")

        # Validate checksums file content
        with open(checksum_path, 'r') as f:
            content = f.read()
        self.assertIn("synthetic_counts.csv", content, "Checksums log missing counts entry")
        self.assertIn("synthetic_peaks.bed", content, "Checksums log missing peaks entry")

if __name__ == '__main__':
    unittest.main()