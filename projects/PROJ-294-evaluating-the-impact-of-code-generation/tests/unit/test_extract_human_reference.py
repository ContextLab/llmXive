"""
Unit tests for T011: extract_human_reference.py
"""
import os
import sys
import json
import tempfile
import unittest
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from unittest.mock import patch, MagicMock

# Add project root to path if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from extract_human_reference import extract_human_references, main
from utils import set_task_id, setup_logging

class TestExtractHumanReference(unittest.TestCase):
    
    def setUp(self):
        """Create temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = os.path.join(self.temp_dir, "data", "raw")
        self.generated_dir = os.path.join(self.temp_dir, "data", "generated")
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.generated_dir, exist_ok=True)
        
        # Create a mock parquet file
        self.parquet_path = os.path.join(self.raw_dir, "humaneval.parquet")
        data = {
            "task_id": ["HumanEval/0", "HumanEval/1"],
            "prompt": ["def add(a, b):\n    pass", "def multiply(a, b):\n    pass"],
            "canonical_solution": ["return a + b", "return a * b"],
            "test": ["assert add(1, 2) == 3", "assert multiply(2, 3) == 6"],
            "entry_point": ["add", "multiply"]
        }
        df = pd.DataFrame(data)
        table = pa.Table.from_pandas(df)
        pq.write_table(table, self.parquet_path)
        
        self.output_path = os.path.join(self.generated_dir, "human_samples.json")

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('extract_human_reference.setup_logging')
    @patch('extract_human_reference.get_logger')
    @patch('extract_human_reference.set_task_id')
    def test_extract_successful(self, mock_set_task, mock_get_logger, mock_setup_log):
        """Test successful extraction of human references."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_setup_log.return_value = mock_logger
        
        count = extract_human_references(self.parquet_path, self.output_path)
        
        self.assertEqual(count, 2)
        self.assertTrue(os.path.exists(self.output_path))
        
        # Verify content
        with open(self.output_path, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 2)
        
        # Parse first line
        record = json.loads(lines[0])
        self.assertEqual(record["task_id"], "HumanEval/0")
        self.assertEqual(record["prompt"], "def add(a, b):\n    pass")
        self.assertEqual(record["canonical_solution"], "return a + b")
        
        # Verify logging
        mock_logger.info.assert_called()

    @patch('extract_human_reference.setup_logging')
    @patch('extract_human_reference.get_logger')
    @patch('extract_human_reference.set_task_id')
    def test_input_not_found(self, mock_set_task, mock_get_logger, mock_setup_log):
        """Test that RuntimeError is raised if input file is missing."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_setup_log.return_value = mock_logger
        
        missing_path = os.path.join(self.raw_dir, "nonexistent.parquet")
        
        with self.assertRaises(RuntimeError) as context:
            extract_human_references(missing_path, self.output_path)
        
        self.assertIn("Input file not found", str(context.exception))

    @patch('extract_human_reference.extract_human_references')
    @patch('extract_human_reference.setup_logging')
    @patch('extract_human_reference.set_task_id')
    def test_main_success(self, mock_set_task, mock_setup_log, mock_extract):
        """Test main function returns 0 on success."""
        mock_logger = MagicMock()
        mock_setup_log.return_value = mock_logger
        mock_extract.return_value = 164
        
        result = main()
        
        self.assertEqual(result, 0)
        mock_extract.assert_called_once()

    @patch('extract_human_reference.extract_human_references')
    @patch('extract_human_reference.setup_logging')
    @patch('extract_human_reference.set_task_id')
    def test_main_failure(self, mock_set_task, mock_setup_log, mock_extract):
        """Test main function returns 1 on failure."""
        mock_logger = MagicMock()
        mock_setup_log.return_value = mock_logger
        mock_extract.side_effect = RuntimeError("Test error")
        
        result = main()
        
        self.assertEqual(result, 1)
        mock_logger.error.assert_called()

if __name__ == '__main__':
    unittest.main()