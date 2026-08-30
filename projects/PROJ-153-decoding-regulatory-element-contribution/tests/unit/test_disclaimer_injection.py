"""
Unit tests for T027: Disclaimer injection into report outputs.

These tests verify that:
1. Markdown files receive the correct disclaimer text
2. PDF files get a companion disclaimer file and metadata update
3. Duplicate disclaimers are not added
4. Files that don't exist are handled gracefully
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code_10_add_disclaimer import (
    inject_markdown_disclaimer,
    inject_pdf_disclaimer,
    DISCLAIMER_TEXT
)


class TestMarkdownDisclaimerInjection:
    """Tests for markdown disclaimer injection."""
    
    def setup_method(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = Path(self.test_dir) / "test_report.md"
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_add_disclaimer_to_empty_file(self):
        """Test adding disclaimer to an empty file."""
        self.test_file.write_text("")
        result = inject_markdown_disclaimer(self.test_file)
        
        assert result is True
        content = self.test_file.read_text()
        assert DISCLAIMER_TEXT in content
        assert "---" in content
    
    def test_add_disclaimer_to_file_with_content(self):
        """Test adding disclaimer to a file with existing content."""
        self.test_file.write_text("# Test Report\n\nSome content here.\n")
        result = inject_markdown_disclaimer(self.test_file)
        
        assert result is True
        content = self.test_file.read_text()
        assert "# Test Report" in content
        assert "Some content here." in content
        assert DISCLAIMER_TEXT in content
    
    def test_no_duplicate_disclaimer(self):
        """Test that duplicate disclaimers are not added."""
        self.test_file.write_text(f"# Report\n\n{DISCLAIMER_TEXT}\n")
        result = inject_markdown_disclaimer(self.test_file)
        
        assert result is True
        content = self.test_file.read_text()
        # Count occurrences of the disclaimer
        count = content.count(DISCLAIMER_TEXT)
        assert count == 1, "Disclaimer should not be duplicated"
    
    def test_missing_file_handling(self):
        """Test that missing files are handled gracefully."""
        missing_file = Path(self.test_dir) / "nonexistent.md"
        result = inject_markdown_disclaimer(missing_file)
        
        assert result is False
    
    def test_file_without_trailing_newline(self):
        """Test handling of files without trailing newlines."""
        self.test_file.write_text("# Report\nContent without newline")
        result = inject_markdown_disclaimer(self.test_file)
        
        assert result is True
        content = self.test_file.read_text()
        assert DISCLAIMER_TEXT in content
        # Should have proper formatting
        assert "---\n" in content


class TestPDFDisclaimerInjection:
    """Tests for PDF disclaimer injection."""
    
    def setup_method(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.test_pdf = Path(self.test_dir) / "test_report.pdf"
        # Create a minimal valid PDF for testing
        self.test_pdf.write_text(
            "%PDF-1.4\n"
            "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
            "xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
            "0000000058 00000 n \n0000000115 00000 n \n"
            "trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n199\n%%EOF"
        )
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_create_companion_file(self):
        """Test that a companion disclaimer file is created."""
        result = inject_pdf_disclaimer(self.test_pdf)
        
        assert result is True
        companion_file = self.test_pdf.parent / f"{self.test_pdf.stem}_disclaimer.txt"
        assert companion_file.exists()
        
        content = companion_file.read_text()
        assert DISCLAIMER_TEXT in content
        assert str(self.test_pdf.name) in content
    
    def test_missing_pdf_handling(self):
        """Test that missing PDF files are handled gracefully."""
        missing_pdf = Path(self.test_dir) / "nonexistent.pdf"
        result = inject_pdf_disclaimer(missing_pdf)
        
        assert result is False
    
    def test_metadata_update_attempt(self):
        """Test that metadata update is attempted (may succeed or fail based on pypdf availability)."""
        # This test verifies the logic path, not the actual success
        result = inject_pdf_disclaimer(self.test_pdf)
        assert result is True  # Should succeed even if pypdf is not available


class TestDisclaimerText:
    """Tests for the disclaimer text itself."""
    
    def test_disclaimer_contains_required_phrases(self):
        """Test that the disclaimer contains required phrases."""
        assert "associational" in DISCLAIMER_TEXT.lower()
        assert "not causal" in DISCLAIMER_TEXT.lower()
        assert "correlation" in DISCLAIMER_TEXT.lower()
    
    def test_disclaimer_is_not_empty(self):
        """Test that the disclaimer is not empty."""
        assert len(DISCLAIMER_TEXT) > 50