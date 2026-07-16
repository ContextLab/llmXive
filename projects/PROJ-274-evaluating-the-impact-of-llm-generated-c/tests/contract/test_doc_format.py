"""
Contract test for documentation output format (Task T025).

This test verifies that the documentation generation pipeline produces
output that conforms to the expected Markdown schema as defined in the
project specifications. It ensures that generated docs contain required
sections: Architecture, API Reference, and Setup Instructions.
"""
import json
import os
import re
import tempfile
import pytest
from pathlib import Path

# Constants for expected structure
REQUIRED_SECTIONS = [
    r"#\s*Architecture",
    r"#\s*API\s+Reference",
    r"#\s*Setup\s+Instructions"
]

REQUIRED_FILES_PATTERN = re.compile(r"^data/raw/llm_docs/.*\.md$")


def load_generated_docs(doc_dir: str) -> dict:
    """
    Load all generated markdown documentation files from the specified directory.
    
    Args:
        doc_dir: Path to the directory containing generated docs.
        
    Returns:
        Dictionary mapping filename to content string.
    """
    docs = {}
    if not os.path.exists(doc_dir):
        return docs
    
    for filename in os.listdir(doc_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(doc_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                docs[filename] = f.read()
    return docs


def validate_section_presence(content: str, section_patterns: list) -> dict:
    """
    Validate that all required sections are present in the document content.
    
    Args:
        content: The markdown content string.
        section_patterns: List of regex patterns for required sections.
        
    Returns:
        Dictionary with validation results per section.
    """
    results = {}
    for pattern in section_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        results[pattern] = {
            "found": bool(match),
            "pattern": pattern
        }
    return results


def validate_file_structure(doc_dir: str) -> dict:
    """
    Validate that the output directory contains valid markdown files.
    
    Args:
        doc_dir: Path to the directory containing generated docs.
        
    Returns:
        Dictionary with validation status and file list.
    """
    files = []
    valid = True
    error = None
    
    if not os.path.isdir(doc_dir):
        return {
            "valid": False,
            "files": [],
            "error": f"Directory does not exist: {doc_dir}"
        }
    
    for filename in os.listdir(doc_dir):
        if not filename.endswith(".md"):
            valid = False
            error = f"Non-markdown file found: {filename}"
            break
        files.append(filename)
        
    return {
        "valid": valid,
        "files": files,
        "error": error
    }


class TestDocumentationFormat:
    """
    Contract tests for the documentation output format.
    
    These tests ensure that the doc generation pipeline (T027-T031)
    produces output that strictly adheres to the required schema.
    """
    
    @pytest.fixture
    def sample_doc_content(self):
        """Provide a sample valid markdown document for testing."""
        return """# Architecture
        
        This is the architecture section.
        
        # API Reference
        
        ## Function: example_function
        
        Description of the function.
        
        # Setup Instructions
        
        1. Install dependencies
        2. Configure environment
        """
        
    @pytest.fixture
    def sample_invalid_doc_content(self):
        """Provide a sample invalid markdown document (missing sections)."""
        return """# Overview
        
        This document is missing required sections.
        """
        
    def test_required_sections_present(self, sample_doc_content):
        """Verify that all required sections are present in valid content."""
        results = validate_section_presence(sample_doc_content, REQUIRED_SECTIONS)
        
        for pattern, result in results.items():
            assert result["found"], f"Required section pattern '{pattern}' not found in document"
            
    def test_missing_sections_detected(self, sample_invalid_doc_content):
        """Verify that missing sections are correctly detected."""
        results = validate_section_presence(sample_invalid_doc_content, REQUIRED_SECTIONS)
        
        found_count = sum(1 for r in results.values() if r["found"])
        assert found_count < len(REQUIRED_SECTIONS), "Invalid document should be missing at least one section"
        
    def test_file_structure_validation(self, tmp_path):
        """Test validation of the output directory structure."""
        # Create a temporary directory with valid markdown files
        doc_dir = tmp_path / "llm_docs"
        doc_dir.mkdir()
        
        (doc_dir / "repo1.md").write_text("# Architecture\n# API Reference\n# Setup Instructions")
        (doc_dir / "repo2.md").write_text("# Architecture\n# API Reference\n# Setup Instructions")
        
        result = validate_file_structure(str(doc_dir))
        
        assert result["valid"] is True
        assert len(result["files"]) == 2
        assert "repo1.md" in result["files"]
        assert "repo2.md" in result["files"]
        assert result["error"] is None
        
    def test_file_structure_validation_empty_dir(self, tmp_path):
        """Test validation when directory is empty."""
        doc_dir = tmp_path / "llm_docs"
        doc_dir.mkdir()
        
        result = validate_file_structure(str(doc_dir))
        
        assert result["valid"] is True
        assert len(result["files"]) == 0
        
    def test_file_structure_validation_missing_dir(self, tmp_path):
        """Test validation when directory does not exist."""
        doc_dir = tmp_path / "nonexistent"
        
        result = validate_file_structure(str(doc_dir))
        
        assert result["valid"] is False
        assert result["error"] is not None
        
    def test_integration_with_generated_docs(self, tmp_path):
        """
        Integration test: Validate actual generated docs if they exist.
        
        This test will pass if the generation pipeline (T027-T031) has
        successfully created valid documentation files in the expected location.
        """
        # Use the standard project path for generated docs
        # Note: This path is relative to the project root
        project_root = Path(__file__).parent.parent.parent
        doc_dir = project_root / "data" / "raw" / "llm_docs"
        
        if doc_dir.exists():
            docs = load_generated_docs(str(doc_dir))
            
            assert len(docs) > 0, "No documentation files found in output directory"
            
            for filename, content in docs.items():
                # Validate each file
                section_results = validate_section_presence(content, REQUIRED_SECTIONS)
                
                for pattern, result in section_results.items():
                    assert result["found"], (
                        f"Generated file '{filename}' is missing required section "
                        f"matching pattern '{pattern}'"
                    )
        else:
            # If docs don't exist yet, this test is skipped (not failed)
            # This allows the test suite to run before generation is complete
            pytest.skip("Generated documentation directory not found. Run generation pipeline first.")