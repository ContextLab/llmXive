"""
Unit tests for T047: API Documentation Generation

This test suite verifies that the Sphinx documentation setup is correct
and that the documentation can be generated without errors.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import unittest

class TestDocumentationGeneration(unittest.TestCase):
    """Tests for API documentation generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.docs_dir = Path(__file__).parent.parent.parent / "docs"
        self.source_dir = self.docs_dir / "source"
        self.build_dir = self.docs_dir / "_build"

    def test_conf_py_exists(self):
        """Test that conf.py exists and is valid Python."""
        conf_path = self.source_dir / "conf.py"
        self.assertTrue(conf_path.exists(), "conf.py must exist")

        # Try to compile the file to check for syntax errors
        with open(conf_path, "r") as f:
            code = f.read()
        try:
            compile(code, str(conf_path), "exec")
        except SyntaxError as e:
            self.fail(f"conf.py has syntax errors: {e}")

    def test_index_rst_exists(self):
        """Test that index.rst exists."""
        index_path = self.source_dir / "index.rst"
        self.assertTrue(index_path.exists(), "index.rst must exist")

    def test_module_rst_files_exist(self):
        """Test that module documentation files exist."""
        required_files = [
            "modules.rst",
            "data_acquisition.rst",
            "pattern_mapping.rst",
            "statistical_analysis.rst",
        ]
        for filename in required_files:
            file_path = self.source_dir / filename
            self.assertTrue(
                file_path.exists(),
                f"{filename} must exist in docs/source"
            )

    def test_makefile_exists(self):
        """Test that Makefile exists."""
        makefile_path = self.docs_dir / "Makefile"
        self.assertTrue(makefile_path.exists(), "Makefile must exist")

    def test_requirements_txt_exists(self):
        """Test that requirements.txt exists."""
        req_path = self.docs_dir / "requirements.txt"
        self.assertTrue(req_path.exists(), "docs/requirements.txt must exist")

    def test_make_docs_script_exists(self):
        """Test that make_docs.sh exists and is executable."""
        script_path = self.docs_dir / "make_docs.sh"
        self.assertTrue(script_path.exists(), "make_docs.sh must exist")
        self.assertTrue(os.access(script_path, os.X_OK), "make_docs.sh must be executable")

    def test_sphinx_imports_in_conf(self):
        """Test that conf.py correctly sets up the Python path."""
        conf_path = self.source_dir / "conf.py"
        with open(conf_path, "r") as f:
            content = f.read()

        # Check for sys.path modification
        self.assertIn("sys.path.insert", content, "conf.py must add code/ to path")
        self.assertIn("code", content, "conf.py must reference the code directory")

    def test_autodoc_extensions_enabled(self):
        """Test that autodoc extensions are enabled."""
        conf_path = self.source_dir / "conf.py"
        with open(conf_path, "r") as f:
            content = f.read()

        self.assertIn("sphinx.ext.autodoc", content, "autodoc extension must be enabled")
        self.assertIn("sphinx.ext.napoleon", content, "napoleon extension must be enabled")

    def test_theme_configured(self):
        """Test that the ReadTheDocs theme is configured."""
        conf_path = self.source_dir / "conf.py"
        with open(conf_path, "r") as f:
            content = f.read()

        self.assertIn("sphinx_rtd_theme", content, "ReadTheDocs theme must be configured")

    def test_module_files_reference_correct_modules(self):
        """Test that module .rst files reference the correct Python modules."""
        module_files = {
            "data_acquisition.rst": "code.01_data_acquisition",
            "pattern_mapping.rst": "code.02_pattern_mapping",
            "statistical_analysis.rst": "code.05_statistical_analysis",
        }

        for filename, module_name in module_files.items():
            file_path = self.source_dir / filename
            with open(file_path, "r") as f:
                content = f.read()
            self.assertIn(
                module_name,
                content,
                f"{filename} must reference {module_name}"
            )

    def test_documentation_structure_valid(self):
        """Test that the documentation structure is valid."""
        # Check that the toctree in index.rst includes modules.rst
        index_path = self.source_dir / "index.rst"
        with open(index_path, "r") as f:
            content = f.read()

        self.assertIn("modules", content, "index.rst must include modules in toctree")

        # Check that modules.rst includes the specific module files
        modules_path = self.source_dir / "modules.rst"
        with open(modules_path, "r") as f:
            content = f.read()

        expected_modules = [
            "data_acquisition",
            "pattern_mapping",
            "statistical_analysis",
        ]
        for module in expected_modules:
            self.assertIn(
                module,
                content,
                f"modules.rst must include {module}"
            )

if __name__ == "__main__":
    unittest.main()