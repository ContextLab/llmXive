"""
Tests for documentation and configuration files.
Ensures README, docs, and config files are present and valid.
"""

import os
import json
import pytest


class TestDocumentationFiles:
    """Tests for the presence and validity of documentation files."""

    def test_readme_exists(self):
        """Test that README.md exists in the project root."""
        assert os.path.exists("README.md"), "README.md is missing"

    def test_readme_contains_required_sections(self):
        """Test that README.md contains key sections."""
        with open("README.md", "r") as f:
            content = f.read()

        required_sections = [
            "Project Overview",
            "Installation",
            "Usage",
            "Project Structure",
            "Output Artifacts",
        ]

        for section in required_sections:
            assert section in content, f"README.md missing section: {section}"

    def test_design_doc_exists(self):
        """Test that docs/design.md exists."""
        assert os.path.exists("docs/design.md"), "docs/design.md is missing"

    def test_api_doc_exists(self):
        """Test that docs/api.md exists."""
        assert os.path.exists("docs/api.md"), "docs/api.md is missing"

    def test_quickstart_doc_exists(self):
        """Test that docs/quickstart.md exists."""
        assert os.path.exists("docs/quickstart.md"), "docs/quickstart.md is missing"

    def test_contributing_doc_exists(self):
        """Test that docs/contributing.md exists."""
        assert os.path.exists("docs/contributing.md"), "docs/contributing.md is missing"

    def test_requirements_txt_exists(self):
        """Test that requirements.txt exists."""
        assert os.path.exists("requirements.txt"), "requirements.txt is missing"

    def test_requirements_txt_contains_dependencies(self):
        """Test that requirements.txt contains key dependencies."""
        with open("requirements.txt", "r") as f:
            content = f.read()

        required_packages = [
            "pandas",
            "numpy",
            "scipy",
            "statsmodels",
            "psutil",
        ]

        for package in required_packages:
            assert package in content, f"requirements.txt missing package: {package}"

    def test_flake8_config_exists(self):
        """Test that .flake8 configuration exists."""
        assert os.path.exists(".flake8"), ".flake8 is missing"

    def test_pyproject_toml_exists(self):
        """Test that pyproject.toml exists with black settings."""
        assert os.path.exists("pyproject.toml"), "pyproject.toml is missing"

        with open("pyproject.toml", "r") as f:
            content = f.read()

        assert "[tool.black]" in content, "pyproject.toml missing [tool.black] section"
        assert "line-length" in content, "pyproject.toml missing line-length setting"

    def test_gitignore_exists(self):
        """Test that .gitignore exists."""
        assert os.path.exists(".gitignore"), ".gitignore is missing"

    def test_run_pipeline_script_exists(self):
        """Test that run_pipeline.sh exists."""
        assert os.path.exists("run_pipeline.sh"), "run_pipeline.sh is missing"

    def test_run_pipeline_script_is_executable(self):
        """Test that run_pipeline.sh has correct shebang."""
        with open("run_pipeline.sh", "r") as f:
            content = f.read()

        assert content.startswith("#!/bin/bash"), "run_pipeline.sh missing bash shebang"


class TestProjectStructure:
    """Tests for the project directory structure."""

    def test_code_directory_exists(self):
        """Test that code/ directory exists."""
        assert os.path.isdir("code"), "code/ directory is missing"

    def test_data_raw_directory_exists(self):
        """Test that data/raw/ directory exists."""
        assert os.path.isdir("data/raw"), "data/raw/ directory is missing"

    def test_data_interim_directory_exists(self):
        """Test that data/interim/ directory exists."""
        assert os.path.isdir("data/interim"), "data/interim/ directory is missing"

    def test_data_processed_directory_exists(self):
        """Test that data/processed/ directory exists."""
        assert os.path.isdir("data/processed"), "data/processed/ directory is missing"

    def test_tests_directory_exists(self):
        """Test that tests/ directory exists."""
        assert os.path.isdir("tests"), "tests/ directory is missing"

    def test_docs_directory_exists(self):
        """Test that docs/ directory exists."""
        assert os.path.isdir("docs"), "docs/ directory is missing"

    def test_reports_directory_exists(self):
        """Test that reports/ directory exists."""
        assert os.path.isdir("reports"), "reports/ directory is missing"

    def test_core_modules_exist(self):
        """Test that all core Python modules exist."""
        required_modules = [
            "code/__init__.py",
            "code/config.py",
            "code/data_model.py",
            "code/ingest.py",
            "code/preprocess.py",
            "code/analysis.py",
            "code/report.py",
            "code/logging_utils.py",
        ]

        for module in required_modules:
            assert os.path.exists(module), f"Missing module: {module}"

    def test_test_modules_exist(self):
        """Test that all test modules exist."""
        required_tests = [
            "tests/test_ingest.py",
            "tests/test_preprocess.py",
            "tests/test_analysis.py",
            "tests/test_report.py",
            "tests/test_documentation.py",
        ]

        for test in required_tests:
            assert os.path.exists(test), f"Missing test module: {test}"