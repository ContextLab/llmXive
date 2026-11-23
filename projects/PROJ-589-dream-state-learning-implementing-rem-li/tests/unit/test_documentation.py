"""
Unit tests to verify documentation completeness and consistency.
These tests ensure that required documentation files exist and contain
expected content sections.
"""
import os
import unittest
from pathlib import Path

class TestDocumentation(unittest.TestCase):
    """Test cases for documentation artifacts."""

    def setUp(self):
        """Set up paths to documentation files."""
        self.project_root = Path(__file__).parent.parent.parent
        self.docs_dir = self.project_root / "docs"
        self.quickstart_path = self.project_root / "quickstart.md"

    def test_docs_directory_exists(self):
        """Verify that the docs/ directory exists."""
        self.assertTrue(self.docs_dir.exists(), "docs/ directory must exist")

    def test_readme_exists(self):
        """Verify that docs/README.md exists."""
        readme_path = self.docs_dir / "README.md"
        self.assertTrue(readme_path.exists(), "docs/README.md must exist")

    def test_architecture_doc_exists(self):
        """Verify that docs/architecture.md exists."""
        arch_path = self.docs_dir / "architecture.md"
        self.assertTrue(arch_path.exists(), "docs/architecture.md must exist")

    def test_contributing_doc_exists(self):
        """Verify that docs/contributing.md exists."""
        contrib_path = self.docs_dir / "contributing.md"
        self.assertTrue(contrib_path.exists(), "docs/contributing.md must exist")

    def test_api_reference_exists(self):
        """Verify that docs/api_reference.md exists."""
        api_path = self.docs_dir / "api_reference.md"
        self.assertTrue(api_path.exists(), "docs/api_reference.md must exist")

    def test_quickstart_exists(self):
        """Verify that quickstart.md exists at project root."""
        self.assertTrue(self.quickstart_path.exists(), "quickstart.md must exist at project root")

    def test_readme_contains_core_concepts(self):
        """Verify README contains explanation of 'consolidated' state."""
        readme_path = self.docs_dir / "README.md"
        content = readme_path.read_text()
        self.assertIn("Consolidated", content, "README must define 'consolidated' state")
        self.assertIn("Wake Phase", content, "README must describe Wake Phase")
        self.assertIn("Dream Phase", content, "README must describe Dream Phase")

    def test_quickstart_contains_usage_instructions(self):
        """Verify quickstart.md contains usage instructions."""
        content = self.quickstart_path.read_text()
        self.assertIn("python main.py", content, "quickstart.md must contain usage examples")
        self.assertIn("full_comparison", content, "quickstart.md must describe full_comparison mode")
        self.assertIn("temperature_sweep", content, "quickstart.md must describe temperature_sweep mode")

    def test_architecture_contains_data_flow(self):
        """Verify architecture.md describes data flow."""
        arch_path = self.docs_dir / "architecture.md"
        content = arch_path.read_text()
        self.assertIn("Data Flow", content, "architecture.md must describe data flow")
        self.assertIn("Trainer", content, "architecture.md must describe Trainer component")
        self.assertIn("Memory Monitor", content, "architecture.md must describe Memory Monitor")

    def test_api_reference_contains_signatures(self):
        """Verify api_reference.md contains function signatures."""
        api_path = self.docs_dir / "api_reference.md"
        content = api_path.read_text()
        self.assertIn("Config", content, "API reference must document Config")
        self.assertIn("DreamScheduler", content, "API reference must document DreamScheduler")
        self.assertIn("Trainer", content, "API reference must document Trainer")
        self.assertIn("wilcoxon_test", content, "API reference must document statistical tests")
