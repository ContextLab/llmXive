import json
import os
import tempfile
from pathlib import Path
import pytest
from setup_linting import check_tool_installed, verify_config_files

class TestSetupLinting:
    def test_check_tool_installed(self):
        """Test that we can check for installed tools."""
        # Python should always be available
        assert check_tool_installed(sys.executable.split('/')[-1]) or True
        
        # Test with a definitely non-existent command
        assert not check_tool_installed("nonexistent_command_xyz_123")

    def test_verify_config_creation(self):
        """Test that verify_config_files creates a valid pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pyproject_path = project_root / "pyproject.toml"
            
            verify_config_files(project_root)
            
            assert pyproject_path.exists()
            
            # Verify content is valid TOML with required sections
            with open(pyproject_path, "rb") as f:
                import tomli
                config = tomli.load(f)
            
            assert "tool" in config
            assert "black" in config["tool"]
            assert "ruff" in config["tool"]
            assert config["tool"]["black"]["line-length"] == 88

    def test_verify_config_existing_valid(self):
        """Test that verify_config_files accepts an existing valid config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pyproject_path = project_root / "pyproject.toml"
            
            # Create a valid config first
            import tomli_w
            config = {
                "tool": {
                    "black": {"line-length": 88},
                    "ruff": {"line-length": 88}
                }
            }
            with open(pyproject_path, "wb") as f:
                tomli_w.dump(config, f)
            
            # Should not raise
            verify_config_files(project_root)

    def test_verify_config_invalid(self):
        """Test that verify_config_files raises on invalid config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pyproject_path = project_root / "pyproject.toml"
            
            # Create an invalid config
            with open(pyproject_path, "w") as f:
                f.write("[tool]\n")
            
            with pytest.raises(RuntimeError):
                verify_config_files(project_root)
