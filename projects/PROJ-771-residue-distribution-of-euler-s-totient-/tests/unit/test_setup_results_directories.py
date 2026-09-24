import os
import shutil
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_results_directories import setup_results_directories

class TestSetupResultsDirectories:
    """Tests for T001c: Create results/plots/ and results/reports/ directories."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Ensure we start with a clean state
        results_base = Path("results")
        if results_base.exists():
            shutil.rmtree(results_base)
        
        yield
        
        # Cleanup after test
        if results_base.exists():
            shutil.rmtree(results_base)

    def test_setup_results_directories_creates_plots_dir(self):
        """Verify that results/plots/ directory is created."""
        success = setup_results_directories()
        assert success, "setup_results_directories should return True"
        
        plots_dir = Path("results/plots")
        assert plots_dir.exists(), "results/plots/ directory should exist"
        assert plots_dir.is_dir(), "results/plots/ should be a directory"

    def test_setup_results_directories_creates_reports_dir(self):
        """Verify that results/reports/ directory is created."""
        success = setup_results_directories()
        assert success, "setup_results_directories should return True"
        
        reports_dir = Path("results/reports")
        assert reports_dir.exists(), "results/reports/ directory should exist"
        assert reports_dir.is_dir(), "results/reports/ should be a directory"

    def test_setup_results_directories_creates_both_dirs(self):
        """Verify that both directories are created in a single call."""
        success = setup_results_directories()
        assert success, "setup_results_directories should return True"
        
        plots_dir = Path("results/plots")
        reports_dir = Path("results/reports")
        
        assert plots_dir.exists() and plots_dir.is_dir()
        assert reports_dir.exists() and reports_dir.is_dir()

    def test_setup_results_directories_idempotent(self):
        """Verify that calling the function multiple times doesn't cause errors."""
        # First call
        success1 = setup_results_directories()
        assert success1, "First call should succeed"
        
        # Second call (should not raise error due to exist_ok=True)
        success2 = setup_results_directories()
        assert success2, "Second call should also succeed"
        
        # Verify directories still exist
        assert Path("results/plots").exists()
        assert Path("results/reports").exists()
