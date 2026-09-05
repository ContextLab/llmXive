"""
Contract tests for the project directory structure setup.

These tests verify that T001 successfully creates all required directories
for the Statistical Properties of Integer Partitions project.
"""
import os
import pytest
from pathlib import Path

# Define the expected directory structure relative to the project root
EXPECTED_DIRS = [
    "projects/PROJ-799-statistical-properties-of-integer-partit/code",
    "projects/PROJ-799-statistical-properties-of-integer-partit/code/utils",
    "projects/PROJ-799-statistical-properties-of-integer-partit/data/raw",
    "projects/PROJ-799-statistical-properties-of-integer-partit/data/processed",
    "projects/PROJ-799-statistical-properties-of-integer-partit/data/schemas",
    "projects/PROJ-799-statistical-properties-of-integer-partit/tests",
    "projects/PROJ-799-statistical-properties-of-integer-partit/tests/data",
    "projects/PROJ-799-statistical-properties-of-integer-partit/docs",
    "projects/PROJ-799-statistical-properties-of-integer-partit/state",
    "projects/PROJ-799-statistical-properties-of-integer-partit/state/projects",
]

class TestProjectStructure:
    """Test suite for verifying project directory structure creation."""

    @pytest.mark.parametrize("dir_path", EXPECTED_DIRS)
    def test_directory_exists(self, dir_path):
        """Verify that each required directory exists."""
        full_path = Path(dir_path)
        assert full_path.exists(), f"Directory does not exist: {dir_path}"
        assert full_path.is_dir(), f"Path is not a directory: {dir_path}"

    def test_base_project_directory_exists(self):
        """Verify the base project directory exists."""
        base_dir = Path("projects/PROJ-799-statistical-properties-of-integer-partit")
        assert base_dir.exists(), "Base project directory does not exist"
        assert base_dir.is_dir(), "Base project path is not a directory"

    def test_directory_hierarchy_integrity(self):
        """Verify the complete hierarchy is present and accessible."""
        base_dir = Path("projects/PROJ-799-statistical-properties-of-integer-partit")
        
        # Verify key subdirectories are children of the base
        assert (base_dir / "code").is_dir(), "code/ is missing"
        assert (base_dir / "data").is_dir(), "data/ is missing"
        assert (base_dir / "tests").is_dir(), "tests/ is missing"
        assert (base_dir / "docs").is_dir(), "docs/ is missing"
        assert (base_dir / "state").is_dir(), "state/ is missing"

        # Verify nested structure
        assert (base_dir / "code" / "utils").is_dir(), "code/utils/ is missing"
        assert (base_dir / "data" / "raw").is_dir(), "data/raw/ is missing"
        assert (base_dir / "data" / "processed").is_dir(), "data/processed/ is missing"
        assert (base_dir / "data" / "schemas").is_dir(), "data/schemas/ is missing"
        assert (base_dir / "tests" / "data").is_dir(), "tests/data/ is missing"
        assert (base_dir / "state" / "projects").is_dir(), "state/projects/ is missing"