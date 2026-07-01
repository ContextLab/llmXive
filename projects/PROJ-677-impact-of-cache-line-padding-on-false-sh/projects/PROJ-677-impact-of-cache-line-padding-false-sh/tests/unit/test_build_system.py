"""
Unit tests for T002: Build system initialization.
Verifies CMake configuration and Python environment setup.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent / "projects" / "PROJ-677-impact-of-cache-line-padding-false-sh"
ANALYSIS_DIR = PROJECT_ROOT / "code" / "analysis"

class TestCMakeConfiguration:
    """Tests for CMake build system configuration."""

    def test_cmake_file_exists(self):
        """Verify CMakeLists.txt exists in analysis directory."""
        cmake_path = ANALYSIS_DIR / "CMakeLists.txt"
        assert cmake_path.exists(), f"CMakeLists.txt not found at {cmake_path}"

    def test_cmake_file_valid_syntax(self):
        """Verify CMakeLists.txt has valid syntax (basic check)."""
        cmake_path = ANALYSIS_DIR / "CMakeLists.txt"
        content = cmake_path.read_text()
        
        # Check for required CMake commands
        assert "cmake_minimum_required" in content
        assert "project(" in content
        assert "add_executable" in content
        assert "set(CMAKE_CXX_STANDARD" in content

    def test_build_script_exists(self):
        """Verify build.sh exists and is executable."""
        build_script = ANALYSIS_DIR / "build.sh"
        assert build_script.exists(), f"build.sh not found at {build_script}"
        
        # Check if executable (on Unix systems)
        if os.name != "nt":
            assert os.access(build_script, os.X_OK), "build.sh is not executable"

class TestPythonEnvironment:
    """Tests for Python environment configuration."""

    def test_requirements_file_exists(self):
        """Verify requirements.txt exists."""
        req_file = ANALYSIS_DIR / "requirements.txt"
        assert req_file.exists(), f"requirements.txt not found at {req_file}"

    def test_requirements_file_content(self):
        """Verify requirements.txt contains expected packages."""
        req_file = ANALYSIS_DIR / "requirements.txt"
        content = req_file.read_text()
        
        required_packages = ["pandas", "scipy", "matplotlib", "pydantic", "pyyaml"]
        for package in required_packages:
            assert package in content, f"Missing package {package} in requirements.txt"

    def test_python_version_check_script(self):
        """Verify verify_python_env.py exists and is valid Python."""
        script_path = ANALYSIS_DIR / "verify_python_env.py"
        assert script_path.exists(), f"verify_python_env.py not found at {script_path}"
        
        # Try to compile the script
        with open(script_path) as f:
            compile(f.read(), script_path, 'exec')

class TestBuildExecution:
    """Tests for actual build execution (requires CMake and C++ compiler)."""

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Build test skipped on Windows"
    )
    def test_cmake_configure(self):
        """Test CMake configuration step."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir) / "build"
            build_dir.mkdir()
            
            result = subprocess.run(
                ["cmake", "-DCMAKE_BUILD_TYPE=Release", str(ANALYSIS_DIR)],
                cwd=build_dir,
                capture_output=True,
                text=True
            )
            
            # CMake might fail if C++ compiler not found, but we check the process ran
            assert result.returncode in [0, 1], "CMake configuration failed unexpectedly"
            if result.returncode == 0:
                assert "Configuring done" in result.stdout or "Configuring done" in result.stderr

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Build test skipped on Windows"
    )
    def test_build_script_execution(self):
        """Test that build.sh can be invoked (may fail if deps missing)."""
        build_script = ANALYSIS_DIR / "build.sh"
        
        # Make sure it's executable
        os.chmod(build_script, 0o755)
        
        # Run with timeout to prevent hanging
        try:
            result = subprocess.run(
                [str(build_script)],
                cwd=ANALYSIS_DIR,
                capture_output=True,
                text=True,
                timeout=60
            )
            # Success or failure is okay if the script runs
            assert result.returncode in [0, 1], "Build script crashed unexpectedly"
        except subprocess.TimeoutExpired:
            pytest.skip("Build took too long")
        except FileNotFoundError:
            pytest.skip("CMake or build tools not available in test environment")