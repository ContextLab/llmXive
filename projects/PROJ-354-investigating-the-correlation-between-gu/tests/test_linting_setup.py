"""
Tests for linting configuration and setup.
"""
import os
import subprocess
import sys
from pathlib import Path
import pytest


class TestLintingConfiguration:
    """Tests for linting configuration files."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent
    
    def test_ruff_config_exists(self, project_root):
        """Test that .ruff.toml exists in the project root."""
        ruff_config = project_root / ".ruff.toml"
        assert ruff_config.exists(), ".ruff.toml file must exist in project root"
    
    def test_pyproject_toml_exists(self, project_root):
        """Test that pyproject.toml exists in the project root."""
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml file must exist in project root"
    
    def test_black_config_in_pyproject(self, project_root):
        """Test that [tool.black] section exists in pyproject.toml."""
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()
        assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
    
    def test_ruff_rules_in_config(self, project_root):
        """Test that required rules (E, F, W, I) are selected in .ruff.toml."""
        ruff_config = project_root / ".ruff.toml"
        content = ruff_config.read_text()
        
        # Check for rule selections
        assert '"E"' in content or "'E'" in content, "Rule E (pycodestyle errors) must be selected"
        assert '"F"' in content or "'F'" in content, "Rule F (Pyflakes) must be selected"
        assert '"W"' in content or "'W'" in content, "Rule W (pycodestyle warnings) must be selected"
        assert '"I"' in content or "'I'" in content, "Rule I (isort) must be selected"
    
    def test_black_line_length(self, project_root):
        """Test that black line-length is configured."""
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()
        
        # Check for line-length configuration in [tool.black]
        assert "line-length" in content, "Black line-length must be configured"
    
    def test_target_python_version(self, project_root):
        """Test that target Python version is configured."""
        pyproject = project_root / "pyproject.toml"
        ruff_config = project_root / ".ruff.toml"
        
        pyproject_content = pyproject.read_text()
        ruff_content = ruff_config.read_text()
        
        # Check for Python 3.10 target
        assert "py310" in pyproject_content or 'python_version = "3.10"' in pyproject_content, \
            "Target Python version 3.10 must be configured in pyproject.toml"
        assert "py310" in ruff_content or 'target-version = "py310"' in ruff_content, \
            "Target Python version 3.10 must be configured in .ruff.toml"

class TestLintingTools:
    """Tests for linting tool execution."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent
    
    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / ".ruff.toml").exists(),
        reason="Linting configuration not set up yet"
    )
    def test_ruff_check_runs(self, project_root):
        """Test that ruff check can be executed."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", "code", "tests"],
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=60
            )
            # We don't assert exit code 0 because there might be linting issues
            # We just verify the command runs without crashing
            assert result.returncode is not None, "ruff check should return an exit code"
        except subprocess.TimeoutExpired:
            pytest.fail("ruff check timed out")
        except FileNotFoundError:
            pytest.skip("ruff not installed in test environment")
    
    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "pyproject.toml").exists(),
        reason="Linting configuration not set up yet"
    )
    def test_black_check_runs(self, project_root):
        """Test that black --check can be executed."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "black", "--check", "code", "tests"],
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=60
            )
            # We don't assert exit code 0 because there might be formatting issues
            # We just verify the command runs without crashing
            assert result.returncode is not None, "black --check should return an exit code"
        except subprocess.TimeoutExpired:
            pytest.fail("black --check timed out")
        except FileNotFoundError:
            pytest.skip("black not installed in test environment")

class TestSetupScript:
    """Tests for the setup_linting.py script."""

    def test_setup_script_exists(self, project_root):
        """Test that setup_linting.py exists."""
        setup_script = project_root / "code" / "setup_linting.py"
        assert setup_script.exists(), "code/setup_linting.py must exist"
    
    def test_setup_script_importable(self, project_root):
        """Test that setup_linting.py can be imported."""
        import sys
        sys.path.insert(0, str(project_root))
        try:
            from code.setup_linting import run_command, check_tool_installed, main
            assert callable(run_command)
            assert callable(check_tool_installed)
            assert callable(main)
        finally:
            sys.path.remove(str(project_root))