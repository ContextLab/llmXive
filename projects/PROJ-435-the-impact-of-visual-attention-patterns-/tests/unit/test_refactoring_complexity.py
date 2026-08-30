"""
Unit tests for refactoring complexity verification.

These tests verify that the refactored code in T046 meets the
cyclomatic complexity requirement of < 10.
"""
import pytest
import subprocess
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class TestRefactoringComplexity:
    """Tests for cyclomatic complexity verification."""

    @pytest.fixture
    def project_paths(self):
        """Get paths to refactored files."""
        return {
            "fixation_detection": PROJECT_ROOT / "code" / "utils" / "fixation_detection.py",
            "roi_mapping": PROJECT_ROOT / "code" / "utils" / "roi_mapping.py"
        }

    def test_ruff_available(self):
        """Test that ruff is available for complexity checking."""
        try:
            result = subprocess.run(
                ["ruff", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, "ruff is not installed or not in PATH"
        except FileNotFoundError:
            pytest.skip("ruff not available in test environment")

    def test_fixation_detection_complexity(self, project_paths):
        """
        Test that fixation_detection.py has cyclomatic complexity < 10.
        
        This test runs ruff with the C901 rule (McCabe complexity) and
        verifies no functions exceed the threshold.
        """
        file_path = project_paths["fixation_detection"]
        
        if not file_path.exists():
            pytest.fail(f"File not found: {file_path}")

        try:
            result = subprocess.run(
                [
                    "ruff", "check",
                    "--select=C901",
                    "--max-complexity=10",
                    str(file_path)
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Return code 0 means no violations found
            assert result.returncode == 0, (
                f"Cyclomatic complexity violations found in {file_path}:\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
        except subprocess.TimeoutExpired:
            pytest.fail("Complexity check timed out")

    def test_roi_mapping_complexity(self, project_paths):
        """
        Test that roi_mapping.py has cyclomatic complexity < 10.
        """
        file_path = project_paths["roi_mapping"]
        
        if not file_path.exists():
            pytest.fail(f"File not found: {file_path}")

        try:
            result = subprocess.run(
                [
                    "ruff", "check",
                    "--select=C901",
                    "--max-complexity=10",
                    str(file_path)
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            assert result.returncode == 0, (
                f"Cyclomatic complexity violations found in {file_path}:\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
        except subprocess.TimeoutExpired:
            pytest.fail("Complexity check timed out")

    def test_fixation_detection_syntax_valid(self, project_paths):
        """Test that the refactored fixation_detection.py is syntactically valid."""
        file_path = project_paths["fixation_detection"]
        
        try:
            compile(file_path.read_text(), str(file_path), "exec")
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {file_path}: {e}")

    def test_roi_mapping_syntax_valid(self, project_paths):
        """Test that the refactored roi_mapping.py is syntactically valid."""
        file_path = project_paths["roi_mapping"]
        
        try:
            compile(file_path.read_text(), str(file_path), "exec")
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {file_path}: {e}")

    def test_fixation_detection_imports(self, project_paths):
        """Test that fixation_detection.py can be imported."""
        file_path = project_paths["fixation_detection"]
        
        try:
            # Try to import the module
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "fixation_detection",
                file_path
            )
            module = importlib.util.module_from_spec(spec)
            # Don't execute - just check if it parses correctly
            spec.loader.exec_module(module)
        except Exception as e:
            pytest.fail(f"Failed to import {file_path}: {e}")

    def test_roi_mapping_imports(self, project_paths):
        """Test that roi_mapping.py can be imported."""
        file_path = project_paths["roi_mapping"]
        
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "roi_mapping",
                file_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            pytest.fail(f"Failed to import {file_path}: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
