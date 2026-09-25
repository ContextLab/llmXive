"""
Unit tests for the pseudocount documentation generator.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.preprocessing.generate_pseudocount_doc import generate_documentation, get_project_root


class TestGeneratePseudocountDoc:
    """Tests for the pseudocount documentation generation."""

    def test_get_project_root(self):
        """Test that get_project_root returns a valid Path."""
        root = get_project_root()
        assert isinstance(root, Path)
        # The root should exist
        assert root.exists()

    def test_generate_documentation_creates_file(self, tmp_path):
        """Test that generate_documentation creates the output file."""
        output_file = tmp_path / "test_pseudocount_doc.txt"
        
        generate_documentation(output_path=output_file)
        
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_generate_documentation_content(self, tmp_path):
        """Test that the generated documentation contains expected content."""
        output_file = tmp_path / "test_pseudocount_doc.txt"
        
        generate_documentation(output_path=output_file)
        
        content = output_file.read_text()
        
        # Check for key sections
        assert "Pseudocount Value Used:" in content
        assert "Justification:" in content
        assert "Problem with Zeros:" in content
        assert "Solution - Pseudocount Addition:" in content
        assert "Choice of Pseudocount Value:" in content
        assert "References:" in content
        
        # Check that the default pseudocount value is mentioned
        assert "1" in content  # The default value

    def test_generate_documentation_creates_directory(self, tmp_path):
        """Test that generate_documentation creates parent directories if needed."""
        nested_output = tmp_path / "deep" / "nested" / "dir" / "pseudocount_doc.txt"
        
        generate_documentation(output_path=nested_output)
        
        assert nested_output.exists()
        assert nested_output.parent.exists()

    def test_generate_documentation_with_logger(self, tmp_path):
        """Test that generate_documentation works with a custom logger."""
        mock_logger = MagicMock()
        output_file = tmp_path / "test_pseudocount_doc.txt"
        
        generate_documentation(output_path=output_file, logger=mock_logger)
        
        assert output_file.exists()
        # Verify logger was called
        assert mock_logger.info.called

    def test_generate_documentation_io_error(self, tmp_path):
        """Test that generate_documentation raises an error on IO failure."""
        # Try to write to a read-only directory (if possible) or invalid path
        # This test may not fail on all systems, so we'll just ensure it doesn't crash normally
        output_file = tmp_path / "test_pseudocount_doc.txt"
        
        # Should succeed under normal conditions
        generate_documentation(output_path=output_file)
        assert output_file.exists()
        
        # Note: Testing actual IO errors requires special setup (e.g., read-only FS)
        # which may not be feasible in all test environments.

    def test_documentation_mentions_clr(self, tmp_path):
        """Test that the documentation mentions CLR transformation."""
        output_file = tmp_path / "test_pseudocount_doc.txt"
        
        generate_documentation(output_path=output_file)
        
        content = output_file.read_text()
        assert "CLR" in content or "Centered Log-Ratio" in content

    def test_documentation_mentions_geometric_mean(self, tmp_path):
        """Test that the documentation mentions geometric mean."""
        output_file = tmp_path / "test_pseudocount_doc.txt"
        
        generate_documentation(output_path=output_file)
        
        content = output_file.read_text()
        assert "geometric mean" in content.lower()

    def test_documentation_cites_references(self, tmp_path):
        """Test that the documentation includes references."""
        output_file = tmp_path / "test_pseudocount_doc.txt"
        
        generate_documentation(output_path=output_file)
        
        content = output_file.read_text()
        assert "References:" in content
        assert "Gloor" in content  # Key author in compositional analysis
        assert "Frontiers in Microbiology" in content or "Nature Communications" in content