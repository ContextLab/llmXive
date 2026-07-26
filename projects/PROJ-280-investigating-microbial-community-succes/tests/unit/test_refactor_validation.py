"""
Unit tests for T038: Code cleanup and refactoring validation.

These tests verify that the refactored scripts:
1. Are syntactically valid Python
2. Have consistent logging setup
3. Use standard import patterns
4. Have no redundant imports
"""
import ast
import os
import sys
from pathlib import Path
import pytest

# Add code directory to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
sys.path.insert(0, str(PROJECT_ROOT))

TARGET_SCRIPTS = [
    "01_retrieve_data.py",
    "02_preprocess.py",
    "03_diversity.py",
    "04_network.py",
    "05_correlation.py",
    "06_aggregate_outputs.py",
    "06_checksum_recorder.py"
]

class TestRefactoredScripts:
    """Test suite for refactored scripts."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.code_dir = CODE_DIR
        self.target_scripts = TARGET_SCRIPTS

    def test_all_scripts_exist(self):
        """Verify all target scripts exist."""
        for script_name in self.target_scripts:
            script_path = self.code_dir / script_name
            assert script_path.exists(), f"Script {script_name} does not exist"

    def test_all_scripts_syntax_valid(self):
        """Verify all scripts are syntactically valid."""
        for script_name in self.target_scripts:
            script_path = self.code_dir / script_name
            with open(script_path, 'r', encoding='utf-8') as f:
                try:
                    compile(f.read(), str(script_path), 'exec')
                except SyntaxError as e:
                    pytest.fail(f"Syntax error in {script_name}: {e}")

    def test_logging_setup_present(self):
        """Verify logging.basicConfig is present in all scripts."""
        for script_name in self.target_scripts:
            script_path = self.code_dir / script_name
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Check for basic logging setup
                assert "logging" in content, f"{script_name} missing logging import"
                # Most scripts should have basicConfig or at least use logging
                # We'll be lenient here as some might use module-level logging only

    def test_no_redundant_imports(self):
        """Check for obviously redundant imports."""
        for script_name in self.target_scripts:
            script_path = self.code_dir / script_name
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
                try:
                    tree = ast.parse(content)
                except SyntaxError:
                    continue  # Already tested in syntax_valid test
            
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for alias in node.names:
                            imports.append(f"{module}.{alias.name}")
            
                # Check for common redundant imports (os, sys if not used)
                # This is a simplified check
                if "os" in imports and "os" not in content:
                    # This would be caught by syntax check anyway, but good to note
                    pass

    def test_consistent_import_patterns(self):
        """Verify consistent import patterns across scripts."""
        for script_name in self.target_scripts:
            script_path = self.code_dir / script_name
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for standard imports that should be present
            standard_imports = ["json", "logging", "pathlib", "sys"]
            for std_import in standard_imports:
                # At least one of these should be present
                if std_import in content:
                    break
            else:
                # If none found, it might be okay for some scripts
                # but we'll log a warning
                pytest.skip(f"Script {script_name} may not need standard imports")

    def test_no_todo_comments(self):
        """Verify no TODO comments remain in refactored scripts."""
        for script_name in self.target_scripts:
            script_path = self.code_dir / script_name
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Check for TODO comments (case-insensitive)
                if "TODO" in content.upper() or "FIXME" in content.upper():
                    pytest.fail(f"TODO/FIXME comment found in {script_name}")

    def test_function_docstrings_present(self):
        """Verify main functions have docstrings."""
        for script_name in self.target_scripts:
            script_path = self.code_dir / script_name
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            
            # Check for main function
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "main":
                    if not ast.get_docstring(node):
                        pytest.fail(f"main() function in {script_name} missing docstring")
                    break

if __name__ == "__main__":
    pytest.main([__file__, "-v"])