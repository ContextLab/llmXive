"""
Integration tests for data_loader error handling (T049).
Verifies that fetch failures raise RuntimeError without synthetic fallback.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import fetch_dataset, verify_checksums


class TestOpenNeuroFetchErrorHandling:
    """Tests for robust error handling in OpenNeuro fetching (T049)."""

    def test_fetch_raises_runtime_error_on_network_failure(self):
        """
        Verify that fetch_dataset raises RuntimeError when network fails,
        and does NOT fall back to synthetic data.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "raw_data"
            output_dir.mkdir()

            # Mock the subprocess call to simulate network failure
            with patch("data_loader.subprocess.run") as mock_run:
                mock_run.side_effect = Exception("Network timeout - connection refused")

                with pytest.raises(RuntimeError) as exc_info:
                    fetch_dataset(
                        dataset_id="ds000030",
                        output_dir=output_dir,
                        checksums_file=None
                    )

                assert "Failed to fetch dataset" in str(exc_info.value)
                assert "Network timeout" in str(exc_info.value)

                # Verify no synthetic data was created
                assert not any(output_dir.rglob("*"))

    def test_fetch_raises_runtime_error_on_invalid_dataset(self):
        """
        Verify that fetch_dataset raises RuntimeError when dataset ID is invalid,
        and does NOT fall back to synthetic data.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "raw_data"
            output_dir.mkdir()

            # Mock the subprocess call to simulate invalid dataset error
            with patch("data_loader.subprocess.run") as mock_run:
                mock_run.side_effect = Exception("Dataset not found: invalid_ds_123")

                with pytest.raises(RuntimeError) as exc_info:
                    fetch_dataset(
                        dataset_id="invalid_ds_123",
                        output_dir=output_dir,
                        checksums_file=None
                    )

                assert "Failed to fetch dataset" in str(exc_info.value)
                assert "Dataset not found" in str(exc_info.value)

                # Verify no synthetic data was created
                assert not any(output_dir.rglob("*"))

    def test_fetch_raises_runtime_error_on_checksum_mismatch(self):
        """
        Verify that verify_checksums raises RuntimeError when checksums don't match,
        and does NOT proceed with corrupted data.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "raw_data"
            output_dir.mkdir()

            # Create a fake file that will fail checksum
            fake_file = output_dir / "fake_file.nii.gz"
            fake_file.write_text("corrupted data")

            checksums_file = Path(tmpdir) / "checksums.sha256"
            checksums_file.write_text(f"{fake_file.name}  correct_checksum_here\n")

            with pytest.raises(RuntimeError) as exc_info:
                verify_checksums(output_dir, checksums_file)

            assert "Checksum verification failed" in str(exc_info.value)
            assert "fake_file.nii.gz" in str(exc_info.value)

    def test_no_synthetic_fallback_in_fetch_dataset(self):
        """
        Explicitly verify that fetch_dataset does NOT contain any synthetic
        data generation or fallback logic.
        """
        import inspect
        source = inspect.getsource(fetch_dataset)

        # Check that no synthetic data generation patterns exist
        forbidden_patterns = [
            "generate_synthetic",
            "mock_data",
            "fake_data",
            "np.random",
            "synthetic",
            "return synthetic",
            "if not real:",
            "except.*:.*generate",
        ]

        for pattern in forbidden_patterns:
            assert pattern not in source.lower(), (
                f"fetch_dataset contains forbidden pattern '{pattern}' - "
                "no synthetic fallback allowed"
            )

    def test_no_synthetic_fallback_in_verify_checksums(self):
        """
        Explicitly verify that verify_checksums does NOT contain any synthetic
        data generation or fallback logic.
        """
        import inspect
        source = inspect.getsource(verify_checksums)

        # Check that no synthetic data generation patterns exist
        forbidden_patterns = [
            "generate_synthetic",
            "mock_data",
            "fake_data",
            "np.random",
            "synthetic",
            "return synthetic",
            "if not real:",
            "except.*:.*generate",
        ]

        for pattern in forbidden_patterns:
            assert pattern not in source.lower(), (
                f"verify_checksums contains forbidden pattern '{pattern}' - "
                "no synthetic fallback allowed"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
