"""
Unit tests for documentation artifacts.

These tests verify that documentation files exist, are well-formed,
and contain required sections.
"""

import os
import pytest
from pathlib import Path

# Base paths
DOCS_DIR = Path(__file__).parent.parent.parent / "docs"
PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestDocumentationFiles:
    """Test that required documentation files exist."""
    
    def test_readme_exists(self):
        """Verify README.md exists in docs directory."""
        readme_path = DOCS_DIR / "README.md"
        assert readme_path.exists(), f"README.md not found at {readme_path}"
    
    def test_architecture_exists(self):
        """Verify ARCHITECTURE.md exists in docs directory."""
        arch_path = DOCS_DIR / "ARCHITECTURE.md"
        assert arch_path.exists(), f"ARCHITECTURE.md not found at {arch_path}"
    
    def test_pipeline_exists(self):
        """Verify PIPELINE.md exists in docs directory."""
        pipeline_path = DOCS_DIR / "PIPELINE.md"
        assert pipeline_path.exists(), f"PIPELINE.md not found at {pipeline_path}"
    
    def test_contributing_exists(self):
        """Verify CONTRIBUTING.md exists in docs directory."""
        contrib_path = DOCS_DIR / "CONTRIBUTING.md"
        assert contrib_path.exists(), f"CONTRIBUTING.md not found at {contrib_path}"
    
    def test_root_readme_exists(self):
        """Verify README.md exists at project root."""
        root_readme = PROJECT_ROOT / "README.md"
        assert root_readme.exists(), f"Root README.md not found at {root_readme}"


class TestDocumentationContent:
    """Test that documentation files contain required content."""
    
    def _read_file(self, filename: str) -> str:
        """Helper to read file contents."""
        filepath = DOCS_DIR / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def test_readme_has_overview(self):
        """Verify README.md contains an overview section."""
        content = self._read_file("README.md")
        assert "# Overview" in content or "## Overview" in content, \
            "README.md missing Overview section"
    
    def test_readme_has_project_structure(self):
        """Verify README.md documents project structure."""
        content = self._read_file("README.md")
        assert "Project Structure" in content or "project structure" in content, \
            "README.md missing project structure documentation"
    
    def test_readme_has_quick_start(self):
        """Verify README.md contains quick start instructions."""
        content = self._read_file("README.md")
        assert "Quick Start" in content or "quick start" in content, \
            "README.md missing Quick Start section"
    
    def test_readme_has_data_sources(self):
        """Verify README.md documents data sources."""
        content = self._read_file("README.md")
        assert "Data Sources" in content or "data sources" in content, \
            "README.md missing Data Sources section"
    
    def test_readme_has_metrics(self):
        """Verify README.md documents metrics."""
        content = self._read_file("README.md")
        assert "Metrics" in content or "metrics" in content, \
            "README.md missing Metrics section"
    
    def test_architecture_has_high_level_design(self):
        """Verify ARCHITECTURE.md contains high-level design."""
        content = self._read_file("ARCHITECTURE.md")
        assert "High-Level Design" in content or "high-level design" in content, \
            "ARCHITECTURE.md missing High-Level Design section"
    
    def test_architecture_has_module_responsibilities(self):
        """Verify ARCHITECTURE.md documents module responsibilities."""
        content = self._read_file("ARCHITECTURE.md")
        assert "Module Responsibilities" in content or "module responsibilities" in content, \
            "ARCHITECTURE.md missing Module Responsibilities section"
    
    def test_architecture_has_data_flow(self):
        """Verify ARCHITECTURE.md contains data flow diagram."""
        content = self._read_file("ARCHITECTURE.md")
        assert "Data Flow" in content or "data flow" in content, \
            "ARCHITECTURE.md missing Data Flow section"
    
    def test_pipeline_has_execution_order(self):
        """Verify PIPELINE.md documents execution order."""
        content = self._read_file("PIPELINE.md")
        assert "Execution Order" in content or "execution order" in content, \
            "PIPELINE.md missing Execution Order section"
    
    def test_pipeline_has_stages(self):
        """Verify PIPELINE.md lists all pipeline stages."""
        content = self._read_file("PIPELINE.md")
        assert "Stage 1" in content and "Stage 2" in content, \
            "PIPELINE.md missing pipeline stage descriptions"
    
    def test_contributing_has_setup(self):
        """Verify CONTRIBUTING.md contains setup instructions."""
        content = self._read_file("CONTRIBUTING.md")
        assert "Development Setup" in content or "development setup" in content, \
            "CONTRIBUTING.md missing Development Setup section"
    
    def test_contributing_has_testing(self):
        """Verify CONTRIBUTING.md documents testing procedures."""
        content = self._read_file("CONTRIBUTING.md")
        assert "Testing" in content or "testing" in content, \
            "CONTRIBUTING.md missing Testing section"
    
    def test_contributing_has_git_workflow(self):
        """Verify CONTRIBUTING.md documents Git workflow."""
        content = self._read_file("CONTRIBUTING.md")
        assert "Git Workflow" in content or "git workflow" in content, \
            "CONTRIBUTING.md missing Git Workflow section"
    
    def test_root_readme_has_license(self):
        """Verify root README.md contains license information."""
        filepath = PROJECT_ROOT / "README.md"
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "License" in content or "license" in content, \
            "Root README.md missing License section"
    
    def test_root_readme_has_citation(self):
        """Verify root README.md contains citation information."""
        filepath = PROJECT_ROOT / "README.md"
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "Citation" in content or "citation" in content, \
            "Root README.md missing Citation section"

class TestDocumentationFormat:
    """Test that documentation files are well-formed Markdown."""
    
    def test_readme_is_valid_markdown(self):
        """Verify README.md uses proper Markdown syntax."""
        content = self._read_file("README.md")
        # Check for at least one heading
        assert any(line.startswith("#") for line in content.splitlines()), \
            "README.md appears to have no Markdown headings"
    
    def test_architecture_is_valid_markdown(self):
        """Verify ARCHITECTURE.md uses proper Markdown syntax."""
        content = self._read_file("ARCHITECTURE.md")
        assert any(line.startswith("#") for line in content.splitlines()), \
            "ARCHITECTURE.md appears to have no Markdown headings"
    
    def test_pipeline_is_valid_markdown(self):
        """Verify PIPELINE.md uses proper Markdown syntax."""
        content = self._read_file("PIPELINE.md")
        assert any(line.startswith("#") for line in content.splitlines()), \
            "PIPELINE.md appears to have no Markdown headings"
    
    def test_contributing_is_valid_markdown(self):
        """Verify CONTRIBUTING.md uses proper Markdown syntax."""
        content = self._read_file("CONTRIBUTING.md")
        assert any(line.startswith("#") for line in content.splitlines()), \
            "CONTRIBUTING.md appears to have no Markdown headings"
    
    def test_files_are_not_empty(self):
        """Verify all documentation files have content."""
        files = ["README.md", "ARCHITECTURE.md", "PIPELINE.md", "CONTRIBUTING.md"]
        for filename in files:
            content = self._read_file(filename)
            assert len(content.strip()) > 0, f"{filename} is empty"
    
    def test_root_readme_not_empty(self):
        """Verify root README.md has content."""
        filepath = PROJECT_ROOT / "README.md"
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        assert len(content.strip()) > 0, "Root README.md is empty"