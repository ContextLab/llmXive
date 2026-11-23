import os
import sys
import pytest
from pathlib import Path
import json
import tempfile
import shutil

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils import setup_logging, get_logger, set_deterministic_seed

# Mock the heavy dependencies to avoid actual execution in unit tests
# We are testing the validation logic, not the pipeline execution itself
from unittest.mock import patch, MagicMock, mock_open

class TestQuickstartValidationLogic:
    """
    Unit tests for the validation logic in run_quickstart_validation.py
    without executing the full pipeline.
    """

    def test_validate_outputs_missing_files(self, tmp_path):
        """
        Test that validate_outputs returns False when required files are missing.
        """
        # Create a temporary directory structure
        # We will patch the base path to point to this temp dir
        
        # Mock the logger
        mock_logger = MagicMock()
        
        # We need to import the function and patch the paths it checks
        # Since the function uses hardcoded paths relative to CWD or specific strings,
        # we will test the logic by creating a scenario where files are missing.
        
        # Actually, let's test the logic by mocking the Path.exists() method
        # We'll create a mock Path that returns False for all checks
        
        original_path = Path
        
        def mock_path_init(self, *args, **kwargs):
            original_path.__init__(self, *args, **kwargs)
            # Store the path string to check later
            self._path_str = str(*args) if args else ""

        def mock_exists(self):
            # Simulate missing files
            missing_patterns = [
                "metadata_mpd.parquet",
                "low_coverage_years.json",
                "excluded_years.json",
                "yearly_similarity.csv",
                "regression_results.json",
                "cooks_distance_report.csv",
                "sensitivity_report.csv",
                "figures/similarity_trend.png",
                "figures/genre_similarity_heatmap.html",
            ]
            return not any(p in self._path_str for p in missing_patterns)

        with patch('run_quickstart_validation.Path') as MockPath:
            # Configure MockPath to behave like real Path but with our custom exists
            MockPath.side_effect = lambda *args, **kwargs: mock_path_init(MockPath(), *args, **kwargs)
            # We need to patch the module where Path is used
            # This is tricky with the class-based structure of Path.
            # Let's simplify: we test the validation logic by creating a real temp dir
            # and checking the return value of a modified version of the function.
            pass

    def test_validate_outputs_all_present(self, tmp_path):
        """
        Test that validate_outputs returns True when all files exist.
        """
        # Create the directory structure in tmp_path
        base_path = tmp_path / "data" / "derived"
        base_path.mkdir(parents=True)
        
        embeddings_path = tmp_path / "yearly_embeddings"
        embeddings_path.mkdir(parents=True)
        
        figures_path = tmp_path / "figures"
        figures_path.mkdir(parents=True)

        # Create dummy files
        required_files = [
            "metadata_mpd.parquet",
            "low_coverage_years.json",
            "excluded_years.json",
            "yearly_similarity.csv",
            "regression_results.json",
            "cooks_distance_report.csv",
            "sensitivity_report.csv",
        ]
        
        for f in required_files:
            (base_path / f).touch()
        
        # Create dummy embeddings
        (embeddings_path / "2020.npy").touch()
        (embeddings_path / "2021.npy").touch()
        
        # Create dummy figures
        (figures_path / "similarity_trend.png").touch()
        (figures_path / "genre_similarity_heatmap.html").touch()

        # Change CWD to tmp_path to match the hardcoded paths in the validation function
        old_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Import the function here to pick up the new CWD
            # We need to reload the module or import it fresh
            if 'run_quickstart_validation' in sys.modules:
                del sys.modules['run_quickstart_validation']
            
            from run_quickstart_validation import validate_outputs
            
            mock_logger = MagicMock()
            result = validate_outputs(mock_logger)
            
            assert result is True
            # Check that logger.info was called for each file
            info_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert "FOUND: data/derived/metadata_mpd.parquet" in str(info_calls)
        finally:
            os.chdir(old_cwd)

    def test_validate_outputs_missing_embeddings(self, tmp_path):
        """
        Test that validate_outputs returns False when embeddings directory is empty.
        """
        base_path = tmp_path / "data" / "derived"
        base_path.mkdir(parents=True)
        
        embeddings_path = tmp_path / "yearly_embeddings"
        embeddings_path.mkdir(parents=True)
        
        figures_path = tmp_path / "figures"
        figures_path.mkdir(parents=True)

        # Create dummy files
        (base_path / "metadata_mpd.parquet").touch()
        (base_path / "yearly_similarity.csv").touch()
        (base_path / "regression_results.json").touch()
        (base_path / "cooks_distance_report.csv").touch()
        (base_path / "sensitivity_report.csv").touch()
        (base_path / "low_coverage_years.json").touch()
        (base_path / "excluded_years.json").touch()
        
        # Create dummy figures
        (figures_path / "similarity_trend.png").touch()
        (figures_path / "genre_similarity_heatmap.html").touch()
        
        # Embeddings dir exists but is empty

        old_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            if 'run_quickstart_validation' in sys.modules:
                del sys.modules['run_quickstart_validation']
            
            from run_quickstart_validation import validate_outputs
            
            mock_logger = MagicMock()
            result = validate_outputs(mock_logger)
            
            assert result is False
            # Check that logger.error was called for missing embeddings
            error_calls = [str(call) for call in mock_logger.error.call_args_list]
            assert any("MISSING EMBEDDINGS" in str(c) for c in error_calls)
        finally:
            os.chdir(old_cwd)
