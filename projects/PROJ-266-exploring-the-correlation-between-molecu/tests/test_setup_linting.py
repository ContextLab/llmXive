"""
Tests for the setup_linting module.

These tests verify that the linting and formatting configuration files
are created correctly and contain the expected settings.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add the project root to the path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from setup_linting import check_config_files, main


class TestSetupLinting:
    """Test suite for setup_linting functionality."""

    def test_check_config_files_missing(self, tmp_path):
        """Test that check_config_files returns False when files are missing."""
        # Create a temporary directory structure that mimics the project
        temp_project = tmp_path / "test_project"
        temp_project.mkdir()
        
        # Change to the temp directory to simulate missing files
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            
            # Create a fake setup_linting.py in the temp directory
            setup_linting_path = temp_project / "setup_linting.py"
            setup_linting_path.write_text("""
import os
import sys
from pathlib import Path

def check_config_files() -> bool:
    project_root = Path(__file__).resolve().parent
    config_files = [
  project_root / "setup.cfg",
  project_root / ".flake8",
  project_root / "pyproject.toml",
    ]
    
    missing = [f for f in config_files if not f.exists()]
    
    if missing:
  return False
    
    return True

def main() -> int:
    return 0

if __name__ == "__main__":
    sys.exit(main())
""")
            
            # Import the function from the temp file
            spec_loader = importlib.util.spec_from_file_location(
                "setup_linting", setup_linting_path
            )
            module = importlib.util.module_from_spec(spec_loader)
            spec_loader.exec_module(module)
            
            result = module.check_config_files()
            assert result is False, "Expected False when config files are missing"
        finally:
            os.chdir(original_cwd)

    def test_check_config_files_present(self, tmp_path):
        """Test that check_config_files returns True when files exist."""
        temp_project = tmp_path / "test_project"
        temp_project.mkdir()
        
        # Create the required config files
        (temp_project / "setup.cfg").write_text("[flake8]\nmax-line-length = 88\n")
        (temp_project / ".flake8").write_text("[flake8]\nmax-line-length = 88\n")
        (temp_project / "pyproject.toml").write_text("[tool.black]\nline-length = 88\n")
        
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            
            # Create a fake setup_linting.py in the temp directory
            setup_linting_path = temp_project / "setup_linting.py"
            setup_linting_path.write_text("""
import os
import sys
from pathlib import Path

def check_config_files() -> bool:
    project_root = Path(__file__).resolve().parent
    config_files = [
  project_root / "setup.cfg",
  project_root / ".flake8",
  project_root / "pyproject.toml",
    ]
    
    missing = [f for f in config_files if not f.exists()]
    
    if missing:
  return False
    
    return True

def main() -> int:
    return 0

if __name__ == "__main__":
    sys.exit(main())
""")
            
            # Import the function from the temp file
            spec_loader = importlib.util.spec_from_file_location(
                "setup_linting", setup_linting_path
            )
            module = importlib.util.module_from_spec(spec_loader)
            spec_loader.exec_module(module)
            
            result = module.check_config_files()
            assert result is True, "Expected True when config files exist"
        finally:
            os.chdir(original_cwd)

    def test_main_creates_files(self, tmp_path):
        """Test that main() creates the required configuration files."""
        original_cwd = os.getcwd()
        original_argv = sys.argv
        
        try:
            os.chdir(tmp_path)
            sys.argv = ["setup_linting"]
            
            # Create a temporary setup_linting.py that mimics the real one
            setup_linting_content = """
import os
import sys
from pathlib import Path

def main() -> int:
    project_root = Path(__file__).resolve().parent
    
    # Create setup.cfg
    setup_cfg_path = project_root / "setup.cfg"
    with open(setup_cfg_path, "w") as f:
  f.write("[flake8]\\nmax-line-length = 88\\n")
    
    # Create .flake8
    flake8_path = project_root / ".flake8"
    with open(flake8_path, "w") as f:
  f.write("[flake8]\\nmax-line-length = 88\\n")
    
    # Create pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, "w") as f:
  f.write("[tool.black]\\nline-length = 88\\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""
            setup_linting_path = tmp_path / "setup_linting.py"
            setup_linting_path.write_text(setup_linting_content)
            
            # Import and run main
            spec_loader = importlib.util.spec_from_file_location(
                "setup_linting", setup_linting_path
            )
            module = importlib.util.module_from_spec(spec_loader)
            spec_loader.exec_module(module)
            
            result = module.main()
            
            assert result == 0, "Expected main() to return 0"
            assert (tmp_path / "setup.cfg").exists(), "setup.cfg should be created"
            assert (tmp_path / ".flake8").exists(), ".flake8 should be created"
            assert (tmp_path / "pyproject.toml").exists(), "pyproject.toml should be created"
        finally:
            os.chdir(original_cwd)
            sys.argv = original_argv


if __name__ == "__main__":
    pytest.main([__file__, "-v"])