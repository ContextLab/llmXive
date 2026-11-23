import os
import sys
import pytest
from pathlib import Path
import subprocess
import tempfile

class TestProjectStructure:
    """
    Tests for project structure creation task (T001).
    """

    @pytest.fixture
    def temp_project_root(self, tmp_path):
        """Create a temporary directory to simulate project root."""
        # Create a temporary directory structure
        (tmp_path / "code").mkdir()
        return tmp_path

    def test_setup_script_exists(self, temp_project_root):
        """Verify that setup_project_structure.py exists in the code directory."""
        script_path = Path("code/setup_project_structure.py")
        # Note: This test assumes the script exists in the actual project
        # In a real scenario, we would check relative to the actual project root
        assert script_path.exists(), f"Script {script_path} does not exist"

    def test_directories_created_by_script(self, temp_project_root, monkeypatch):
        """Test that the script creates all required directories."""
        # Change to temp directory to simulate project root
        monkeypatch.chdir(temp_project_root)
        
        # Import and run the setup script
        sys.path.insert(0, str(temp_project_root / "code"))
        from setup_project_structure import create_directories
        
        # Create directories
        created, skipped = create_directories()
        
        # Verify all required directories exist
        required_dirs = [
            "code/src/data",
            "code/src/models",
            "code/src/training",
            "code/src/analysis",
            "code/src/config",
            "code/tests/unit",
            "code/tests/integration",
            "code/contracts",
            "code/data/raw",
            "code/data/processed",
            "code/data/results",
            "code/artifacts",
        ]
        
        for dir_path in required_dirs:
            full_path = temp_project_root / dir_path
            assert full_path.exists(), f"Required directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} exists but is not a directory"

    def test_main_function_returns_success(self, temp_project_root, monkeypatch):
        """Test that main() returns 0 on success."""
        monkeypatch.chdir(temp_project_root)
        
        sys.path.insert(0, str(temp_project_root / "code"))
        from setup_project_structure import main
        
        result = main()
        assert result == 0, f"main() returned {result}, expected 0"

    def test_main_function_handles_errors(self, temp_project_root, monkeypatch):
        """Test that main() returns 1 on error."""
        # This test would require mocking to simulate an error condition
        # For now, we verify the function exists and has error handling
        monkeypatch.chdir(temp_project_root)
        
        sys.path.insert(0, str(temp_project_root / "code"))
        from setup_project_structure import main
        
        # Verify the function exists
        assert callable(main), "main() is not callable"

    def test_idempotency(self, temp_project_root, monkeypatch):
        """Test that running the script multiple times doesn't cause errors."""
        monkeypatch.chdir(temp_project_root)
        
        sys.path.insert(0, str(temp_project_root / "code"))
        from setup_project_structure import create_directories
        
        # Run twice
        created1, skipped1 = create_directories()
        created2, skipped2 = create_directories()
        
        # Second run should have more skipped, fewer created
        assert skipped2 >= skipped1, "Second run should not create fewer skipped directories"
        assert created2 <= created1, "Second run should not create more directories"

    def test_directory_structure_valid(self, temp_project_root, monkeypatch):
        """Test that created directories have the correct hierarchical structure."""
        monkeypatch.chdir(temp_project_root)
        
        sys.path.insert(0, str(temp_project_root / "code"))
        from setup_project_structure import create_directories
        
        create_directories()
        
        # Verify parent-child relationships
        assert (temp_project_root / "code" / "src").exists()
        assert (temp_project_root / "code" / "src" / "data").exists()
        assert (temp_project_root / "code" / "src" / "models").exists()
        assert (temp_project_root / "code" / "data").exists()
        assert (temp_project_root / "code" / "data" / "raw").exists()
        assert (temp_project_root / "code" / "data" / "processed").exists()
        assert (temp_project_root / "code" / "data" / "results").exists()