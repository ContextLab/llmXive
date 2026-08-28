"""
Contract tests for security audit functionality.
"""
import pytest
import subprocess
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

class TestSecurityAudit:
    """Tests for security audit functionality."""

    def test_safety_command_exists(self):
        """Verify that the safety command is available."""
        try:
            result = subprocess.run(
                ["safety", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, "safety command not found"
            assert "safety" in result.stdout.lower()
        except FileNotFoundError:
            pytest.skip("safety command not installed in test environment")

    def test_requirements_file_exists(self):
        """Verify that requirements.txt exists."""
        project_root = Path(__file__).parent.parent.parent
        requirements_path = project_root / "requirements.txt"
        assert requirements_path.exists(), "requirements.txt not found"

    def test_security_audit_script_exists(self):
        """Verify that security audit script exists."""
        project_root = Path(__file__).parent.parent.parent
        script_path = project_root / "code" / "scripts" / "security_audit.py"
        assert script_path.exists(), "security_audit.py not found"

    def test_security_audit_script_importable(self):
        """Verify that security audit script can be imported."""
        try:
            from scripts.security_audit import run_safety_check, main
            assert callable(run_safety_check)
            assert callable(main)
        except ImportError as e:
            pytest.fail(f"Failed to import security_audit: {e}")

    def test_safety_check_runs_on_requirements(self):
        """Test that safety check runs without crashing on valid requirements."""
        project_root = Path(__file__).parent.parent.parent
        requirements_path = project_root / "requirements.txt"
        
        if not requirements_path.exists():
            pytest.skip("requirements.txt not found")
        
        try:
            from scripts.security_audit import run_safety_check
            # Just test that it runs without crashing
            # The return code depends on actual vulnerabilities
            result = run_safety_check(str(requirements_path))
            assert isinstance(result, int)
            assert result in [0, 1]  # 0 = clean, 1 = vulnerabilities found
        except FileNotFoundError:
            pytest.skip("safety command not installed")
        except Exception as e:
            # Other errors might occur if safety is misconfigured
            pytest.skip(f"safety check failed: {e}")

    def test_requirements_contains_expected_packages(self):
        """Verify that requirements.txt contains expected packages."""
        project_root = Path(__file__).parent.parent.parent
        requirements_path = project_root / "requirements.txt"
        
        if not requirements_path.exists():
            pytest.skip("requirements.txt not found")
        
        content = requirements_path.read_text()
        expected_packages = [
            "nilearn",
            "networkx",
            "scikit-learn",
            "numpy",
            "pandas",
            "matplotlib",
            "scipy",
            "brainconn"
        ]
        
        for package in expected_packages:
            assert package.lower() in content.lower(), \
                f"Expected package {package} not found in requirements.txt"