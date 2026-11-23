"""
Tests for T008a: Generate Research Sources
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code directory to path for imports
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from ingestion.source_search import generate_candidate_sources_file, generate_research_md_draft

class TestSourceSearch:
    def test_generate_candidate_sources_file_creates_file(self, tmp_path):
        """Test that the candidate sources file is created and contains expected content."""
        output_file = tmp_path / "candidate_sources.txt"
        
        generate_candidate_sources_file(output_file)
        
        assert output_file.exists(), "Candidate sources file was not created"
        
        content = output_file.read_text()
        assert "# Candidate Data Sources" in content
        assert "Materials Project API" in content
        assert "OpenAlloy Database" in content
        assert "Status: candidate" in content
        assert "End of candidate sources list" in content

    def test_generate_research_md_draft_creates_file(self, tmp_path):
        """Test that the research.md draft is created and contains expected content."""
        output_file = tmp_path / "research.md"
        
        generate_research_md_draft(output_file)
        
        assert output_file.exists(), "Research.md draft was not created"
        
        content = output_file.read_text()
        assert "# Research Sources" in content
        assert "Initial Draft" in content
        assert "Materials Project" in content
        assert "Status: Candidate" in content

    def test_file_format_correctness(self, tmp_path):
        """Test that the generated files have correct formatting."""
        sources_file = tmp_path / "sources.txt"
        research_file = tmp_path / "research.md"
        
        generate_candidate_sources_file(sources_file)
        generate_research_md_draft(research_file)
        
        sources_content = sources_file.read_text()
        research_content = research_file.read_text()
        
        # Check for specific sections
        assert "## API and Database Sources" in sources_content
        assert "## Literature Sources" in sources_content
        
        assert "## 1. Primary Data Repositories" in research_content
        assert "## 2. Literature for PDF Scraping" in research_content
        
        # Check for DOI presence
        assert "10.1007/s10853-018-2567-x" in sources_content
        assert "10.1007/s10853-018-2567-x" in research_content
