"""
Integration tests for the CLI Orchestrator (run_pipeline.py).
Verifies the orchestration logic, citation gate, and synthetic fallback.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.cli.run_pipeline import main as run_pipeline_main
from src.cli.validate_citations import main as validate_citations_main
from src.data.generators.structural_validation_generator import main as generate_structural_main
from src.data.processing.feature_engineering import main as feature_engineering_main

class TestPipelineSyntheticFallback:
    """Tests for synthetic data fallback logic."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace mimicking project structure."""
        temp_dir = tempfile.mkdtemp()
        # Create necessary directories
        (Path(temp_dir) / "data" / "raw").mkdir(parents=True)
        (Path(temp_dir) / "data" / "processed").mkdir(parents=True)
        (Path(temp_dir) / "src" / "cli").mkdir(parents=True)
        (Path(temp_dir) / "src" / "data" / "generators").mkdir(parents=True)
        (Path(temp_dir) / "src" / "data" / "processing").mkdir(parents=True)
        # Create a dummy research.md with valid citations to pass the gate
        (Path(temp_dir) / "research.md").write_text(
            "This is a test.\nCitation: (Smith et al., 2023)\n"
        )
        yield temp_dir
        shutil.rmtree(temp_dir)

    @patch('src.cli.run_pipeline.validate_citations_main')
    @patch('src.cli.run_pipeline.generate_structural_main')
    @patch('src.cli.run_pipeline.feature_engineering_main')
    def test_ci_mode_invokes_generator_when_no_data(
        self, mock_fe, mock_gen, mock_citations, temp_workspace
    ):
        """
        When CI=true and data/raw/ is empty, the generator MUST be invoked.
        """
        # Set CI environment
        os.environ["CI"] = "true"
        
        # Ensure data/raw is empty (fixture creates it empty)
        data_raw = Path(temp_workspace) / "data" / "raw"
        assert not any(data_raw.iterdir())

        # Mock the citation validator to succeed (exit 0)
        mock_citations.side_effect = SystemExit(0)

        # Change CWD to temp_workspace to simulate project root
        old_cwd = os.getcwd()
        os.chdir(temp_workspace)

        try:
            # Run with ingest stage
            with pytest.raises(SystemExit) as exc_info:
                run_pipeline_main()
            
            # Should exit 0 on success
            assert exc_info.value.code == 0

            # Verify generator was called
            assert mock_gen.called, "Generator should be invoked in CI mode when data is missing"
            # Verify feature engineering was called
            assert mock_fe.called, "Feature engineering should be invoked after generation"
        finally:
            os.chdir(old_cwd)
            del os.environ["CI"]

    @patch('src.cli.run_pipeline.validate_citations_main')
    def test_citation_gate_aborts_on_failure(self, mock_citations, temp_workspace):
        """
        If citation validation fails, the pipeline MUST abort immediately.
        """
        os.environ["CI"] = "true"
        
        # Mock citation validator to fail (exit 1)
        mock_citations.side_effect = SystemExit(1)

        old_cwd = os.getcwd()
        os.chdir(temp_workspace)

        try:
            with pytest.raises(SystemExit) as exc_info:
                run_pipeline_main()
            
            # Should exit 1 due to citation failure
            assert exc_info.value.code == 1
        finally:
            os.chdir(old_cwd)
            del os.environ["CI"]

class TestPipelineCLI:
    """Tests for CLI argument parsing and dry-run."""

    @patch('src.cli.run_pipeline.validate_citations_main')
    def test_dry_run_validates_imports(self, mock_citations, temp_workspace):
        """
        Dry run should validate imports and exit 0.
        """
        mock_citations.side_effect = SystemExit(0)
        
        old_cwd = os.getcwd()
        os.chdir(temp_workspace)

        try:
            # Simulate command line args
            with patch('sys.argv', ['run_pipeline.py', '--dry-run']):
                with pytest.raises(SystemExit) as exc_info:
                    run_pipeline_main()
                
                assert exc_info.value.code == 0
        finally:
            os.chdir(old_cwd)
