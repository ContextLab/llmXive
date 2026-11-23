"""
Test suite for T001b: Project Structure Creation.
Verifies that the required directory hierarchy exists after running setup_project.py.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil


class TestProjectStructure:
    """Tests for the project structure creation logic."""
    
    def test_directory_hierarchy_exists(self):
        """
        Verify that all required directories exist at the project root.
        
        Required structure:
        - data/raw
        - data/processed
        - code
        - code/tests
        - code/utils
        - code/models
        - docs
        """
        # Determine project root (parent of this test file's directory)
        test_file = Path(__file__).resolve()
        project_root = test_file.parent.parent
        
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "code/tests",
            "code/utils",
            "code/models",
            "docs",
        ]
        
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Required directory missing: {full_path}"
            assert full_path.is_dir(), f"Path is not a directory: {full_path}"
    
    def test_data_and_code_are_siblings(self):
        """
        Verify that data/ and code/ are sibling directories at project root,
        not nested within each other.
        """
        test_file = Path(__file__).resolve()
        project_root = test_file.parent.parent
        
        data_dir = project_root / "data"
        code_dir = project_root / "code"
        
        assert data_dir.exists(), "data/ directory missing"
        assert code_dir.exists(), "code/ directory missing"
        
        # Verify they are siblings (same parent)
        assert data_dir.parent == code_dir.parent, \
            "data/ and code/ are not siblings"
        
        # Verify neither is nested in the other
        assert not data_dir in code_dir.parents, "data/ is nested inside code/"
        assert not code_dir in data_dir.parents, "code/ is nested inside data/"
    
    def test_nested_structure_correctness(self):
        """
        Verify the nested structure is correct:
        - data/raw exists
        - data/processed exists
        - code/tests exists
        - code/utils exists
        - code/models exists
        """
        test_file = Path(__file__).resolve()
        project_root = test_file.parent.parent
        
        nested_dirs = [
            "data/raw",
            "data/processed",
            "code/tests",
            "code/utils",
            "code/models",
        ]
        
        for dir_path in nested_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Nested directory missing: {full_path}"
            assert full_path.is_dir(), f"Path is not a directory: {full_path}"
    
    def test_no_unexpected_nesting(self):
        """
        Verify that the structure doesn't have unexpected nesting
        (e.g., code/data or data/code).
        """
        test_file = Path(__file__).resolve()
        project_root = test_file.parent.parent
        
        # These should NOT exist based on the spec
        forbidden_paths = [
            "code/data",
            "data/code",
            "code/data/raw",
            "data/code/raw",
        ]
        
        for path_str in forbidden_paths:
            full_path = project_root / path_str
            # We don't assert they don't exist (they might be created by other processes),
            # but we log if they do
            if full_path.exists():
                pytest.fail(f"Unexpected nested directory found: {full_path}")
    
    def test_setup_script_runs_successfully(self):
        """
        Verify that the setup script can be executed and creates the structure.
        """
        test_file = Path(__file__).resolve()
        project_root = test_file.parent.parent
        setup_script = project_root / "code" / "setup_project.py"
        
        assert setup_script.exists(), "setup_project.py not found"
        
        # Import and run the function directly
        import sys
        sys.path.insert(0, str(project_root / "code"))
        
        from setup_project import create_structure
        
        # Run the structure creation
        result = create_structure()
        
        assert result is True, "create_structure() did not return True"
        
        # Verify structure exists after running
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "code/tests",
            "code/utils",
            "code/models",
            "docs",
        ]
        
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Directory missing after setup: {full_path}"
            assert full_path.is_dir(), f"Path is not a directory after setup: {full_path}"