import os
import sys
from pathlib import Path
import pytest

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_linting import ensure_ruff_config, ensure_black_config, update_requirements

class TestLintingConfig:
    def test_ruff_config_exists(self, tmp_path):
        """Test that ruff config file is created or found."""
        # Create a temporary directory structure mimicking the project
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        # Mock the Path resolution by temporarily changing cwd
        original_cwd = os.getcwd()
        try:
            os.chdir(code_dir)
            # Re-import to pick up the new cwd
            import importlib
            import setup_linting
            importlib.reload(setup_linting)
            
            # Call the function
            result = setup_linting.ensure_ruff_config()
            
            # Check file exists
            config_path = code_dir / ".ruff.toml"
            assert config_path.exists()
            assert result is True
            
            # Check content has expected sections
            content = config_path.read_text()
            assert "[lint]" in content
            assert "[format]" in content
        finally:
            os.chdir(original_cwd)

    def test_black_config_exists(self, tmp_path):
        """Test that black config file is created or found."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        original_cwd = os.getcwd()
        try:
            os.chdir(code_dir)
            import importlib
            import setup_linting
            importlib.reload(setup_linting)
            
            result = setup_linting.ensure_black_config()
            
            config_path = code_dir / ".black.toml"
            assert config_path.exists()
            assert result is True
            
            content = config_path.read_text()
            assert "[tool.black]" in content
            assert "line-length" in content
        finally:
            os.chdir(original_cwd)

    def test_requirements_updated(self, tmp_path):
        """Test that requirements.txt is updated with linting tools."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        req_path = code_dir / "requirements.txt"
        req_path.write_text("pandas==2.0.0\n")
        
        original_cwd = os.getcwd()
        try:
            os.chdir(code_dir)
            import importlib
            import setup_linting
            importlib.reload(setup_linting)
            
            result = setup_linting.update_requirements()
            
            content = req_path.read_text()
            assert "ruff" in content
            assert "black" in content
            assert result is True
        finally:
            os.chdir(original_cwd)

    def test_main_function(self, tmp_path):
        """Test the main function orchestrates all setup steps."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        req_path = code_dir / "requirements.txt"
        req_path.write_text("pandas==2.0.0\n")
        
        original_cwd = os.getcwd()
        try:
            os.chdir(code_dir)
            import importlib
            import setup_linting
            importlib.reload(setup_linting)
            
            result = setup_linting.main()
            
            assert result == 0
            assert (code_dir / ".ruff.toml").exists()
            assert (code_dir / ".black.toml").exists()
            assert "ruff" in req_path.read_text()
        finally:
            os.chdir(original_cwd)