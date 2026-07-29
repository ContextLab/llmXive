"""
Unit tests for the ingestion scaffold (T005).

Verifies that the ingestion module structure is correct and 
the main entry point initializes without import errors.
"""
import pytest
import sys
from pathlib import Path
import os

# Add code root to path
code_root = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

class TestIngestionScaffold:
    """Tests for the ingestion scaffold module."""

    def test_ingestion_module_importable(self):
        """Verify that the ingestion module can be imported."""
        try:
            from ingestion import LiteratureAggregator, DataCleaner, DataValidator
            from ingestion import run_pipeline, calculate_md5
            assert LiteratureAggregator is not None
            assert DataCleaner is not None
            assert DataValidator is not None
        except ImportError as e:
            pytest.fail(f"Failed to import ingestion module: {e}")

    def test_scaffold_main_exists(self):
        """Verify that the scaffold main function exists."""
        from ingestion.scaffold import main
        assert callable(main)

    def test_directory_structure_accessible(self):
        """Verify that config paths for data directories exist."""
        from config import get_data_raw_dir, get_data_processed_dir
        
        raw_dir = get_data_raw_dir()
        processed_dir = get_data_processed_dir()
        
        assert isinstance(raw_dir, Path)
        assert isinstance(processed_dir, Path)
        # We don't assert existence of the actual folder here as T001 
        # (directory creation) might be handled by the runner script,
        # but we verify the config returns a Path object.

    def test_seed_initialization_available(self):
        """Verify that seed initialization is available for the pipeline."""
        from seed import init_reproducibility
        assert callable(init_reproducibility)