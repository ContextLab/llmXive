import pytest
import sys
import os
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

class TestConsolidation:
    """Test that T1214 consolidation was successful."""

    def test_cleanup_utils_raises_error(self):
        """Verify that cleanup_utils.py raises ImportError when imported."""
        with pytest.raises(ImportError, match="consolidated into utils.py"):
            import cleanup_utils

    def test_profiler_raises_error(self):
        """Verify that profiler.py raises ImportError when imported."""
        with pytest.raises(ImportError, match="consolidated into utils.py"):
            import profiler

    def test_utils_has_setup_logging(self):
        """Verify setup_logging exists in utils."""
        from utils import setup_logging
        logger = setup_logging("INFO")
        assert logger is not None
        assert logger.name == "llmXive_pipeline"

    def test_utils_has_pin_random_seed(self):
        """Verify pin_random_seed exists in utils."""
        from utils import pin_random_seed
        pin_random_seed(42)
        # If we get here, the function exists and ran without error

    def test_utils_has_compute_file_checksum(self):
        """Verify compute_file_checksum exists in utils."""
        from utils import compute_file_checksum
        # Create a temporary test file
        test_file = code_dir / "test_checksum_temp.txt"
        try:
            test_file.write_text("test content")
            checksum = compute_file_checksum(str(test_file))
            assert len(checksum) == 64  # SHA256 hex length
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_utils_has_profiling_functions(self):
        """Verify profiling functions from profiler.py exist in utils."""
        from utils import (
            start_profiling,
            stop_profiling,
            add_profile_entry,
            get_profile_summary,
            profile_function,
            profile_block
        )
        
        start_profiling()
        add_profile_entry({"name": "test", "duration_seconds": 1.0, "status": "success"})
        summary = get_profile_summary()
        assert summary["total_duration"] == 1.0
        assert summary["successful"] == 1

    def test_utils_has_cleanup_functions(self):
        """Verify cleanup functions from cleanup_utils.py exist in utils."""
        from utils import validate_data_integrity, log_dataset_stats
        # These functions should be callable without error
        assert callable(validate_data_integrity)
        assert callable(log_dataset_stats)
