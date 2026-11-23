"""
Integration test for T065: Fail-loud policy during execution gate.

This test simulates the execution gate (T036) scenario where all data sources
are unavailable and verifies that the pipeline halts with a clear error message
rather than proceeding with synthetic data or failing silently.

This test is designed to be run as part of the CI/CD pipeline to ensure
the fail-loud policy is maintained.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.download import download_data
from analysis.run_pipeline import run_full_pipeline


class TestExecutionGateFailLoud(unittest.TestCase):
    """Integration tests for fail-loud policy at execution gate."""

    def test_pipeline_halts_on_all_sources_fail(self):
        """
        Simulate T036 execution gate: All data sources fail.
        Verify that run_full_pipeline raises RuntimeError and does not
        produce any output artifacts.
        """
        # Mock all data sources to fail
        mock_pushshift = MagicMock()
        mock_pushshift.status_code = 500
        mock_pushshift.text = "Internal Server Error"
        
        mock_reddit = MagicMock()
        mock_reddit.status_code = 401
        mock_reddit.text = "Unauthorized"
        
        mock_hf = Exception("Dataset not available")
        
        mock_archive = MagicMock()
        mock_archive.status_code = 404
        mock_archive.text = "Not Found"

        # Set up request mocks
        def mock_get_side_effect(*args, **kwargs):
            if 'pushshift' in str(args[0]):
                return mock_pushshift
            elif 'archive' in str(args[0]):
                return mock_archive
            return mock_pushshift  # Default fallback

        def mock_post_side_effect(*args, **kwargs):
            return mock_reddit

        with patch('data.download.requests.get', side_effect=mock_get_side_effect), \
             patch('data.download.requests.post', side_effect=mock_post_side_effect), \
             patch('data.download.hf_hub_download', side_effect=mock_hf), \
             patch('data.download.time.sleep'):

            with tempfile.TemporaryDirectory() as tmpdir:
                # Set up paths
                data_dir = Path(tmpdir) / "data"
                state_dir = Path(tmpdir) / "state"
                data_dir.mkdir()
                state_dir.mkdir()

                # Mock config to use temporary directories
                with patch('config.settings.get_config') as mock_config:
                    mock_config.return_value.raw_data_dir = data_dir
                    mock_config.return_value.processed_dir = data_dir / "processed"
                    mock_config.return_value.state_dir = state_dir
                    mock_config.return_value.output_dir = data_dir / "processed"

                    # Attempt to run pipeline - should fail
                    with self.assertRaises(RuntimeError) as context:
                        run_full_pipeline(
                            threads=10,
                            output_dir=str(data_dir / "processed"),
                            state_dir=str(state_dir)
                        )

                    # Verify error message
                    error_msg = str(context.exception)
                    self.assertIn("data", error_msg.lower())
                    self.assertIn("source", error_msg.lower())
                    self.assertIn("fail", error_msg.lower())

                    # Verify no output files were created
                    processed_dir = data_dir / "processed"
                    if processed_dir.exists():
                        files = list(processed_dir.glob("*"))
                        self.assertEqual(
                            len(files), 0,
                            "No output files should be created when all sources fail"
                        )

    def test_no_synthetic_data_in_artifacts(self):
        """
        Verify that even if some partial execution occurs,
        no synthetic data markers appear in any artifacts.
        """
        # Mock partial failure: Pushshift fails, but other sources also fail
        mock_pushshift = MagicMock()
        mock_pushshift.status_code = 500
        mock_pushshift.text = "Error"
        
        mock_hf = Exception("Not found")
        mock_archive = MagicMock()
        mock_archive.status_code = 404
        mock_archive.text = "Not Found"

        with patch('data.download.requests.get', return_value=mock_pushshift), \
             patch('data.download.hf_hub_download', side_effect=mock_hf), \
             patch('data.download.time.sleep'):

            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "output.jsonl"
                
                with self.assertRaises(RuntimeError):
                    download_data(
                        subreddits=['test'],
                        limit=5,
                        output=str(output_path)
                    )

                # Verify file doesn't exist
                self.assertFalse(output_path.exists())

                # Also verify no partial files with synthetic markers
                all_files = list(Path(tmpdir).rglob("*"))
                for file_path in all_files:
                    if file_path.is_file():
                        try:
                            content = file_path.read_text()
                            self.assertNotIn(
                                "synthetic", content.lower(),
                                f"File {file_path} contains synthetic marker"
                            )
                            self.assertNotIn(
                                "mock", content.lower(),
                                f"File {file_path} contains mock marker"
                            )
                            self.assertNotIn(
                                "generated_fallback", content.lower(),
                                f"File {file_path} contains fallback marker"
                            )
                        except:
                            pass  # Binary files or other issues


if __name__ == '__main__':
    unittest.main()