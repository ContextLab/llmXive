import os
import shutil
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_results_directories import setup_results_directories

class TestResultsDirectoriesIntegration:
    """Integration test for T001c: Verify results directories work with the pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        results_base = Path("results")
        if results_base.exists():
            shutil.rmtree(results_base)
        
        yield
        
        # Cleanup after test
        if results_base.exists():
            shutil.rmtree(results_base)

    def test_results_directories_ready_for_pipeline(self):
        """
        Integration test: Verify that after running setup_results_directories,
        the pipeline can write placeholder files to the created directories.
        """
        # Setup the directories (T001c)
        success = setup_results_directories()
        assert success, "setup_results_directories must succeed"
        
        # Simulate pipeline writing files (e.g., a plot and a report)
        plots_dir = Path("results/plots")
        reports_dir = Path("results/reports")
        
        test_plot = plots_dir / "test_plot.png"
        test_report = reports_dir / "test_report.md"
        
        # Write test files
        test_plot.write_bytes(b"PNG_PLACEHOLDER")
        test_report.write_text("# Test Report\n\nThis is a test.")
        
        # Verify files exist and are writable
        assert test_plot.exists(), "Pipeline should be able to write to results/plots/"
        assert test_report.exists(), "Pipeline should be able to write to results/reports/"
        
        # Verify content
        assert test_plot.read_bytes() == b"PNG_PLACEHOLDER"
        assert test_report.read_text() == "# Test Report\n\nThis is a test."
        
        # Cleanup test files
        test_plot.unlink()
        test_report.unlink()
        
        # Verify directories still exist after file deletion
        assert plots_dir.exists()
        assert reports_dir.exists()

    def test_results_directories_structure_matches_spec(self):
        """
        Verify the directory structure matches the project specification:
        - results/plots/
        - results/reports/
        """
        setup_results_directories()
        
        expected_structure = {
            "results": {
                "plots": [],
                "reports": []
            }
        }
        
        # Verify root
        assert Path("results").exists()
        assert Path("results").is_dir()
        
        # Verify subdirectories
        assert Path("results/plots").exists()
        assert Path("results/plots").is_dir()
        
        assert Path("results/reports").exists()
        assert Path("results/reports").is_dir()
        
        # Verify no extra unexpected directories at top level of results
        contents = set([p.name for p in Path("results").iterdir()])
        expected = {"plots", "reports"}
        assert contents == expected, f"Unexpected directories found: {contents - expected}"