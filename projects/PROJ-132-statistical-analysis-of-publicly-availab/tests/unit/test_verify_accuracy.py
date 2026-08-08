"""
Unit tests for the Verified Accuracy Gate (Task T004)

Tests for src/data/verify_accuracy.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.verify_accuracy import (
    verify_huggingface_dataset,
    verify_accuracy_gate,
    write_verification_report,
    main,
    DATA_SOURCES
)

class TestVerifyAccuracyGate:
    """Test suite for the Verified Accuracy Gate implementation."""

    @patch('src.data.verify_accuracy.load_dataset')
    def test_verify_huggingface_dataset_success(self, mock_load_dataset):
        """Test successful verification of a HuggingFace dataset."""
        # Setup mock
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([{"species": "test", "lat": 1.0, "lon": 1.0}]))
        mock_load_dataset.return_value = mock_dataset

        # Create test config
        config = {
            "name": "Test Dataset",
            "source_id": "test/dataset",
            "type": "huggingface"
        }

        # Run verification
        result = verify_huggingface_dataset(config)

        # Assert results
        assert result["status"] == "verified"
        assert result["source"] == "test/dataset"
        assert result["details"]["accessible"] is True
        assert "first_example_keys" in result["details"]

    @patch('src.data.verify_accuracy.load_dataset')
    def test_verify_huggingface_dataset_failure(self, mock_load_dataset):
        """Test verification failure when dataset is not accessible."""
        # Setup mock to raise an exception
        mock_load_dataset.side_effect = Exception("Dataset not found")

        # Create test config
        config = {
            "name": "Test Dataset",
            "source_id": "invalid/dataset",
            "type": "huggingface"
        }

        # Run verification
        result = verify_huggingface_dataset(config)

        # Assert results
        assert result["status"] == "failed"
        assert "Dataset not found" in result["details"]["error"]

    def test_verify_accuracy_gate_structure(self):
        """Test that the main verification function returns the expected structure."""
        # We can't run the full gate without real datasets, but we can check structure
        # by mocking the individual verification calls
        with patch('src.data.verify_accuracy.verify_huggingface_dataset') as mock_verify:
            # Setup mock to return a verified status
            mock_verify.return_value = {
                "source": "test/dataset",
                "status": "verified",
                "checksum": None,
                "details": {"accessible": True},
                "timestamp": "2024-01-01T00:00:00+00:00"
            }

            # Run the gate
            results = verify_accuracy_gate()

            # Assert structure
            assert "verification_timestamp" in results
            assert "sources_checked" in results
            assert "all_verified" in results
            assert "results" in results
            assert results["sources_checked"] == len(DATA_SOURCES)
            assert len(results["results"]) == len(DATA_SOURCES)

    def test_write_verification_report(self):
        """Test that the report is written correctly to disk."""
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the PROVENANCE_DIR
            import src.data.verify_accuracy as va_module
            original_provenance_dir = va_module.PROVENANCE_DIR
            va_module.PROVENANCE_DIR = Path(tmpdir)

            try:
                test_results = {
                    "verification_timestamp": "2024-01-01T00:00:00+00:00",
                    "sources_checked": 2,
                    "all_verified": True,
                    "results": [
                        {
                            "source": "test1",
                            "status": "verified",
                            "checksum": None,
                            "details": {},
                            "timestamp": "2024-01-01T00:00:00+00:00"
                        }
                    ]
                }

                # Write the report
                write_verification_report(test_results)

                # Verify file was created
                output_file = Path(tmpdir) / "accuracy_verification.json"
                assert output_file.exists()

                # Verify content
                with open(output_file, 'r') as f:
                    written_results = json.load(f)
                
                assert written_results["all_verified"] is True
                assert len(written_results["results"]) == 1
            finally:
                # Restore original directory
                va_module.PROVENANCE_DIR = original_provenance_dir

    def test_main_success_path(self):
        """Test the main function when all verifications succeed."""
        with patch('src.data.verify_accuracy.verify_accuracy_gate') as mock_gate:
            with patch('src.data.verify_accuracy.write_verification_report'):
                # Setup mock to return success
                mock_gate.return_value = {
                    "all_verified": True,
                    "results": []
                }

                # Run main
                result = main()

                # Assert success
                assert result == 0

    def test_main_failure_path(self):
        """Test the main function when verification fails."""
        with patch('src.data.verify_accuracy.verify_accuracy_gate') as mock_gate:
            with patch('src.data.verify_accuracy.write_verification_report'):
                # Setup mock to return failure
                mock_gate.return_value = {
                    "all_verified": False,
                    "results": [
                        {"source": "bad/source", "status": "failed"}
                    ]
                }

                # Run main and expect RuntimeError
                with pytest.raises(RuntimeError) as exc_info:
                    main()

                # Assert error message contains expected text
                assert "Accuracy Gate Verification Failed" in str(exc_info.value)

    def test_main_exception_handling(self):
        """Test that main handles unexpected exceptions gracefully."""
        with patch('src.data.verify_accuracy.verify_accuracy_gate') as mock_gate:
            # Setup mock to raise an unexpected exception
            mock_gate.side_effect = ValueError("Unexpected error")

            # Run main and expect return code 1
            result = main()
            assert result == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])