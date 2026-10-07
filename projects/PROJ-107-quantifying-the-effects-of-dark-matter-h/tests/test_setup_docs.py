"""
Tests for the setup_docs module (T001c).
Verifies that the required directory structure and placeholder files are created.
"""
import os
import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_docs import create_docs_structure
from utils.config import get_project_root


class TestSetupDocs:
    """Test cases for the documentation and output directory setup."""

    def test_directories_created(self, tmp_path):
        """
        Verify that the docs/, outputs/, outputs/figures/, and outputs/reports/
        directories are created when the function runs.
        """
        # We need to mock the project root to use the temp directory
        # Since get_project_root() is hardcoded to look for a specific marker or parent,
        # we will test the logic by checking the side effects of the function 
        # if we can control the environment, or simply verify the function exists 
        # and runs without error in a real context.
        
        # For this specific test, we assume the function runs against the actual project root.
        # We verify the existence of the paths defined in the task.
        
        project_root = get_project_root()
        docs_dir = project_root / "docs"
        outputs_dir = project_root / "outputs"
        figures_dir = outputs_dir / "figures"
        reports_dir = outputs_dir / "reports"
        
        # Run the setup
        create_docs_structure()
        
        # Assertions
        assert docs_dir.exists(), f"docs/ directory not created at {docs_dir}"
        assert outputs_dir.exists(), f"outputs/ directory not created at {outputs_dir}"
        assert figures_dir.exists(), f"outputs/figures/ directory not created at {figures_dir}"
        assert reports_dir.exists(), f"outputs/reports/ directory not created at {reports_dir}"

    def test_placeholder_files_created(self):
        """
        Verify that docs/quickstart.md and docs/README.md are created.
        """
        project_root = get_project_root()
        docs_dir = project_root / "docs"
        quickstart_path = docs_dir / "quickstart.md"
        readme_path = docs_dir / "README.md"
        
        # Run the setup (idempotent)
        create_docs_structure()
        
        assert quickstart_path.exists(), "docs/quickstart.md not created"
        assert readme_path.exists(), "docs/README.md not created"
        
        # Verify content is not empty
        assert quickstart_path.stat().st_size > 0, "docs/quickstart.md is empty"
        assert readme_path.stat().st_size > 0, "docs/README.md is empty"

    def test_structure_persistence(self):
        """
        Verify that running the script multiple times does not corrupt the structure.
        """
        project_root = get_project_root()
        
        # Run twice
        create_docs_structure()
        create_docs_structure()
        
        docs_dir = project_root / "docs"
        outputs_dir = project_root / "outputs"
        
        assert docs_dir.exists()
        assert outputs_dir.exists()