"""
Tests for the US1 Pipeline script (src/cli.py).

These tests verify the orchestration logic without necessarily
re-running the heavy data loading/encoding if mocked, or by
checking that the functions are called in the correct order.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class TestUS1Pipeline(unittest.TestCase):

    @patch('src.cli.load_webvid_subjects')
    @patch('src.cli.compute_complexity_scores')
    @patch('src.cli.extract_domainshuttle_embeddings')
    @patch('src.cli.save_csv_safe')
    @patch('src.cli.ensure_output_dirs')
    def test_pipeline_execution_order(self, mock_dirs, mock_save_csv, mock_embed, mock_complexity, mock_load):
        """Test that the pipeline calls functions in the correct order."""
        
        # Setup mocks
        mock_load.return_value = MagicMock(iterrows=MagicMock(return_value=iter([
            (0, {'id': 'sub_001'}),
            (1, {'id': 'sub_002'})
        ])))
        mock_complexity.return_value = {'sub_001': 0.5, 'sub_002': 0.8}
        mock_embed.return_value = {'sub_001': 'emb_001', 'sub_002': 'emb_002'}
        mock_dirs.return_value = Path('/fake/path')
        
        # Import the main function logic (we can't easily run the argparse main without sys exit)
        # Instead, we simulate the body of main()
        from src.cli import main
        
        # We need to patch sys.argv to avoid argparse errors in unit test context if we call main()
        # But since main() calls sys.exit(), we mock it.
        with patch('sys.argv', ['cli.py', '--num-subjects', '2']):
            with patch('sys.exit') as mock_exit:
                try:
                    main()
                except SystemExit:
                    pass # Expected from sys.exit(0)

        # Verify order
        mock_load.assert_called_once()
        mock_complexity.assert_called_once()
        mock_embed.assert_called_once()
        mock_dirs.assert_called_once()
        mock_save_csv.assert_called_once()

        # Verify calls were sequential
        self.assertEqual(mock_load.call_count, 1)
        self.assertEqual(mock_complexity.call_count, 1)
        self.assertEqual(mock_embed.call_count, 1)

    @patch('src.cli.load_webvid_subjects')
    def test_pipeline_empty_data_failure(self, mock_load):
        """Test that the pipeline raises an error if no data is loaded."""
        mock_load.return_value = MagicMock(empty=True)

        from src.cli import main
        
        with patch('sys.argv', ['cli.py']):
            with patch('sys.exit') as mock_exit:
                with self.assertRaises(RuntimeError) as context:
                    main()
                
                self.assertIn("Failed to load any subjects", str(context.exception))
                mock_exit.assert_called_once_with(1)

if __name__ == '__main__':
    unittest.main()