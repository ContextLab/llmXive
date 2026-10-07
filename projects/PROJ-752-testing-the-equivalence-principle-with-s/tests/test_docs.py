"""
Tests for documentation completeness and consistency.
This task (T042) ensures that all documentation artifacts are present and valid.
"""

import os
import yaml
import pytest
from pathlib import Path

# Base paths
DOCS_DIR = Path("docs")
ROOT_DIR = Path(__file__).parent.parent
CONFIG_FILE = ROOT_DIR / "config.yaml"

class TestDocumentation:
    """Tests for T042: Documentation updates."""

    def test_readme_exists(self):
        """Verify that README.md exists in docs/."""
        readme_path = DOCS_DIR / "README.md"
        assert readme_path.exists(), f"README.md not found at {readme_path}"
        assert readme_path.stat().st_size > 0, "README.md is empty"

    def test_api_reference_exists(self):
        """Verify that api_reference.md exists in docs/."""
        api_ref_path = DOCS_DIR / "api_reference.md"
        assert api_ref_path.exists(), f"api_reference.md not found at {api_ref_path}"
        assert api_ref_path.stat().st_size > 0, "api_reference.md is empty"

    def test_quickstart_exists(self):
        """Verify that quickstart.md exists in docs/."""
        quickstart_path = DOCS_DIR / "quickstart.md"
        assert quickstart_path.exists(), f"quickstart.md not found at {quickstart_path}"
        assert quickstart_path.stat().st_size > 0, "quickstart.md is empty"

    def test_glossary_exists(self):
        """Verify that glossary.md exists in docs/."""
        glossary_path = DOCS_DIR / "glossary.md"
        assert glossary_path.exists(), f"glossary.md not found at {glossary_path}"
        assert glossary_path.stat().st_size > 0, "glossary.md is empty"

    def test_readme_contains_project_overview(self):
        """Verify README.md contains essential sections."""
        readme_path = DOCS_DIR / "README.md"
        content = readme_path.read_text()

        required_sections = [
            "Project Overview",
            "Scientific Context",
            "Project Structure",
            "Quick Start",
            "Key Components",
            "Configuration",
            "API Reference",
            "Research & Benchmarks"
        ]

        for section in required_sections:
            assert section in content, f"Missing section '{section}' in README.md"

    def test_api_reference_contains_modules(self):
        """Verify api_reference.md documents all core modules."""
        api_ref_path = DOCS_DIR / "api_reference.md"
        content = api_ref_path.read_text()

        required_modules = [
            "code/config.py",
            "code/models/entities.py",
            "code/models/dynamics.py",
            "code/models/estimator.py",
            "code/analysis/eotvos.py",
            "code/analysis/validation.py",
            "code/data/ingestion.py",
            "code/data/preprocessing.py",
            "code/cli/main.py",
            "code/utils/logging.py"
        ]

        for module in required_modules:
            assert module in content, f"Missing module documentation for '{module}' in api_reference.md"

    def test_quickstart_contains_commands(self):
        """Verify quickstart.md contains executable commands."""
        quickstart_path = DOCS_DIR / "quickstart.md"
        content = quickstart_path.read_text()

        required_commands = [
            "pip install -r requirements.txt",
            "python code/cli/main.py",
            "python code/scripts/validate_quickstart.py"
        ]

        for cmd in required_commands:
            assert cmd in content, f"Missing command '{cmd}' in quickstart.md"

    def test_config_yaml_valid(self):
        """Verify that config.yaml is valid YAML and contains required keys."""
        assert CONFIG_FILE.exists(), "config.yaml not found"

        try:
            with open(CONFIG_FILE, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"config.yaml is not valid YAML: {e}")

        # Check for benchmark_values section (T048.0d requirement)
        assert "benchmark_values" in config, "Missing 'benchmark_values' in config.yaml"
        # Note: etvos_limit may be None if research is not complete, but the key structure must exist.

    def test_docs_directory_structure(self):
        """Verify that docs/ directory contains expected files."""
        expected_files = [
            "README.md",
            "api_reference.md",
            "quickstart.md",
            "glossary.md"
        ]

        for filename in expected_files:
            file_path = DOCS_DIR / filename
            assert file_path.exists(), f"Expected file {filename} not found in docs/"