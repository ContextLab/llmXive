import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add code to path if running from tests
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup_directories import ensure_directory, main

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as project root for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)

class TestEnsureDirectory:
    def test_creates_new_directory(self, temp_project_root):
        test_path = temp_project_root / "new_dir"
        assert not test_path.exists()
        
        result = ensure_directory(str(test_path))
        
        assert result is True
        assert test_path.exists()
        assert test_path.is_dir()

    def test_returns_true_if_exists(self, temp_project_root):
        test_path = temp_project_root / "existing_dir"
        test_path.mkdir()
        
        result = ensure_directory(str(test_path))
        
        assert result is True

    def test_raises_on_file_collision(self, temp_project_root):
        test_path = temp_project_root / "file.txt"
        test_path.touch()
        
        with pytest.raises(Exception): # ConfigurationError
            ensure_directory(str(test_path))

    def test_creates_nested_directories(self, temp_project_root):
        test_path = temp_project_root / "level1" / "level2" / "level3"
        assert not test_path.exists()
        
        result = ensure_directory(str(test_path))
        
        assert result is True
        assert test_path.exists()
        assert test_path.is_dir()

class TestMain:
    def test_creates_expected_structure(self, temp_project_root):
        # Mock the project name to be relative to temp dir
        # The main function uses a hardcoded name, so we check if it creates it
        
        # We need to patch the main function or verify the result after execution
        # Since main() uses relative paths, running it in temp dir should work
        
        # Note: main() prints logs. We expect it to return 0.
        # We can't easily patch the hardcoded string "PROJ-800..." inside main
        # without refactoring, but we can check the side effects.
        
        # Let's assume the task description implies running this creates the dirs.
        # We will verify the directory existence after calling main.
        
        # To make this testable, we might need to refactor main to accept a base path,
        # but for now, we verify the expected outcome.
        
        # Actually, to strictly test without refactoring, we rely on the fact that
        # main() creates `projects/PROJ-800...` relative to CWD.
        
        result = main()
        
        assert result == 0
        
        project_path = Path("PROJ-800-assessing-parcellation-sensitivity-of-hu")
        assert project_path.exists()
        assert (project_path / "code").exists()
        assert (project_path / "tests").exists()
        assert (project_path / "data").exists()
        assert (project_path / "data" / "raw").exists()
        assert (project_path / "data" / "processed").exists()
        assert (project_path / "data" / "results").exists()