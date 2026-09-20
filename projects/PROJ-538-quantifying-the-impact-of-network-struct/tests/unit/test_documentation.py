"""
Unit tests for documentation completeness and accuracy.

These tests verify that all required documentation files exist
and contain expected content.
"""

import os
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def docs_dir(project_root):
    """Get the docs directory path."""
    return project_root / "docs"


class TestDocumentationFiles:
    """Test that all required documentation files exist."""

    def test_readme_exists(self, project_root):
        """Verify README.md exists at project root."""
        readme = project_root / "README.md"
        assert readme.exists(), "README.md not found at project root"
        assert readme.is_file(), "README.md is not a file"

    def test_analysis_methodology_exists(self, docs_dir):
        """Verify analysis_methodology.md exists."""
        file_path = docs_dir / "analysis_methodology.md"
        assert file_path.exists(), "docs/analysis_methodology.md not found"
        assert file_path.is_file(), "docs/analysis_methodology.md is not a file"

    def test_implementation_guide_exists(self, docs_dir):
        """Verify implementation_guide.md exists."""
        file_path = docs_dir / "implementation_guide.md"
        assert file_path.exists(), "docs/implementation_guide.md not found"
        assert file_path.is_file(), "docs/implementation_guide.md is not a file"

    def test_api_reference_exists(self, docs_dir):
        """Verify api_reference.md exists."""
        file_path = docs_dir / "api_reference.md"
        assert file_path.exists(), "docs/api_reference.md not found"
        assert file_path.is_file(), "docs/api_reference.md is not a file"

    def test_user_guide_exists(self, docs_dir):
        """Verify user_guide.md exists."""
        file_path = docs_dir / "user_guide.md"
        assert file_path.exists(), "docs/user_guide.md not found"
        assert file_path.is_file(), "docs/user_guide.md is not a file"

class TestDocumentationContent:
    """Test that documentation files contain expected content."""

    def test_readme_contains_project_title(self, project_root):
        """Verify README contains project title."""
        readme = project_root / "README.md"
        content = readme.read_text()
        assert "Quantifying the Impact of Network Structure" in content, \
            "README.md missing project title"

    def test_readme_contains_installation_section(self, project_root):
        """Verify README contains installation instructions."""
        readme = project_root / "README.md"
        content = readme.read_text()
        assert "Installation" in content or "installation" in content, \
            "README.md missing installation section"
        assert "pip install" in content, \
            "README.md missing pip install instructions"

    def test_readme_contains_usage_section(self, project_root):
        """Verify README contains usage instructions."""
        readme = project_root / "README.md"
        content = readme.read_text()
        assert "Usage" in content or "usage" in content, \
            "README.md missing usage section"
        assert "python -m code.main" in content, \
            "README.md missing pipeline execution command"

    def test_readme_contains_project_structure(self, project_root):
        """Verify README documents project structure."""
        readme = project_root / "README.md"
        content = readme.read_text()
        assert "code/" in content, "README.md missing code/ directory reference"
        assert "data/" in content, "README.md missing data/ directory reference"
        assert "tests/" in content, "README.md missing tests/ directory reference"

    def test_analysis_methodology_contains_data_sources(self, docs_dir):
        """Verify analysis methodology documents data sources."""
        file_path = docs_dir / "analysis_methodology.md"
        content = file_path.read_text()
        assert "OpenKim" in content, "analysis_methodology.md missing OpenKim reference"
        assert "Materials Cloud" in content, "analysis_methodology.md missing Materials Cloud reference"
        assert "synthetic" in content.lower(), "analysis_methodology.md missing synthetic data description"

    def test_analysis_methodology_contains_network_construction(self, docs_dir):
        """Verify analysis methodology documents network construction."""
        file_path = docs_dir / "analysis_methodology.md"
        content = file_path.read_text()
        assert "Voronoi" in content, "analysis_methodology.md missing Voronoi tessellation reference"
        assert "defect graph" in content.lower(), "analysis_methodology.md missing defect graph description"

    def test_analysis_methodology_contains_metrics(self, docs_dir):
        """Verify analysis methodology documents topological metrics."""
        file_path = docs_dir / "analysis_methodology.md"
        content = file_path.read_text()
        assert "clustering coefficient" in content.lower(), "analysis_methodology.md missing clustering coefficient"
        assert "percolation" in content.lower(), "analysis_methodology.md missing percolation threshold"

    def test_implementation_guide_contains_architecture(self, docs_dir):
        """Verify implementation guide documents architecture."""
        file_path = docs_dir / "implementation_guide.md"
        content = file_path.read_text()
        assert "Architecture" in content or "architecture" in content, \
            "implementation_guide.md missing architecture section"
        assert "code/ingest.py" in content, "implementation_guide.md missing ingest.py reference"
        assert "code/metrics.py" in content, "implementation_guide.md missing metrics.py reference"

    def test_api_reference_contains_modules(self, docs_dir):
        """Verify API reference documents all modules."""
        file_path = docs_dir / "api_reference.md"
        content = file_path.read_text()
        assert "code/config.py" in content, "api_reference.md missing config.py"
        assert "code/ingest.py" in content, "api_reference.md missing ingest.py"
        assert "code/metrics.py" in content, "api_reference.md missing metrics.py"
        assert "code/stats.py" in content, "api_reference.md missing stats.py"
        assert "code/viz.py" in content, "api_reference.md missing viz.py"

    def test_api_reference_contains_models(self, docs_dir):
        """Verify API reference documents Pydantic models."""
        file_path = docs_dir / "api_reference.md"
        content = file_path.read_text()
        assert "AtomicSnapshot" in content, "api_reference.md missing AtomicSnapshot"
        assert "DefectGraph" in content, "api_reference.md missing DefectGraph"
        assert "CorrelationResult" in content, "api_reference.md missing CorrelationResult"

    def test_user_guide_contains_troubleshooting(self, docs_dir):
        """Verify user guide contains troubleshooting section."""
        file_path = docs_dir / "user_guide.md"
        content = file_path.read_text()
        assert "Troubleshooting" in content or "troubleshooting" in content, \
            "user_guide.md missing troubleshooting section"
        assert "DataAvailabilityError" in content, "user_guide.md missing DataAvailabilityError reference"
        assert "VoronoiFailure" in content, "user_guide.md missing VoronoiFailure reference"

    def test_user_guide_contains_output_files(self, docs_dir):
        """Verify user guide documents output files."""
        file_path = docs_dir / "user_guide.md"
        content = file_path.read_text()
        assert "audit_log.json" in content, "user_guide.md missing audit_log.json reference"
        assert "correlation_heatmap.png" in content, "user_guide.md missing correlation_heatmap.png reference"
        assert "sensitivity_report.csv" in content, "user_guide.md missing sensitivity_report.csv reference"

class TestDocumentationQuality:
    """Test documentation quality and completeness."""

    def test_readme_has_no_placeholder_text(self, project_root):
        """Verify README has no placeholder text."""
        readme = project_root / "README.md"
        content = readme.read_text()
        assert "[Insert" not in content, "README.md contains placeholder text"
        assert "TODO" not in content, "README.md contains TODO text"
        assert "FIXME" not in content, "README.md contains FIXME text"

    def test_docs_have_consistent_formatting(self, docs_dir):
        """Verify documentation files use consistent formatting."""
        for file_path in docs_dir.glob("*.md"):
            content = file_path.read_text()
            # Check for markdown headers
            assert "#" in content, f"{file_path.name} missing markdown headers"
            # Check for code blocks
            assert "```" in content, f"{file_path.name} missing code blocks"

    def test_all_modules_documented(self, docs_dir):
        """Verify all code modules are documented in API reference."""
        api_ref = (docs_dir / "api_reference.md").read_text()
        modules = [
            "config.py", "ingest.py", "synthetic.py", "metrics.py",
            "stats.py", "viz.py", "models.py", "utils.py", "interfaces.py", "main.py"
        ]
        for module in modules:
            assert module in api_ref, f"api_reference.md missing {module} documentation"