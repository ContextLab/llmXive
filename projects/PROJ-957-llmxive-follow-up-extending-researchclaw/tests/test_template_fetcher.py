"""
Tests for the template fetcher module (T009b).

These tests verify:
1. URL reading from verified file
2. Protocol content extraction from various HTML structures
3. Content cleaning and normalization
4. File output with correct encoding
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.templates.fetcher import (
    read_verified_url,
    extract_protocol_content,
    clean_html_tags,
    save_protocol_content
)

class TestReadVerifiedUrl:
    """Tests for reading the verified URL file."""
    
    def test_read_existing_url_file(self, tmp_path):
        """Test reading a valid URL file."""
        url_file = tmp_path / "verified_url.txt"
        test_url = "https://example.com/protocol"
        url_file.write_text(test_url)
        
        result = read_verified_url(str(url_file))
        assert result == test_url
    
    def test_read_empty_url_file(self, tmp_path):
        """Test reading an empty URL file raises error."""
        url_file = tmp_path / "verified_url.txt"
        url_file.write_text("")
        
        with pytest.raises(ValueError, match="Verified URL file is empty"):
            read_verified_url(str(url_file))
    
    def test_read_nonexistent_url_file(self, tmp_path):
        """Test reading a non-existent file raises error."""
        url_file = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            read_verified_url(str(url_file))
    
    def test_read_url_with_whitespace(self, tmp_path):
        """Test that whitespace is stripped from URL."""
        url_file = tmp_path / "verified_url.txt"
        test_url = "  https://example.com/protocol  \n"
        url_file.write_text(test_url)
        
        result = read_verified_url(str(url_file))
        assert result == "https://example.com/protocol"

class TestExtractProtocolContent:
    """Tests for extracting protocol content from HTML."""
    
    def test_extract_from_div_protocol(self):
        """Test extraction from <div class='protocol'>."""
        html = """
        <html>
        <body>
            <div class="protocol">
                <p>This is the protocol content.</p>
                <ol>
                    <li>Step 1</li>
                    <li>Step 2</li>
                </ol>
            </div>
        </body>
        </html>
        """
        result = extract_protocol_content(html)
        assert result is not None
        assert "This is the protocol content" in result
        assert "Step 1" in result
    
    def test_extract_from_section_protocol(self):
        """Test extraction from <section class='protocol'>."""
        html = """
        <html>
        <body>
            <section class="protocol">
                Protocol section content here.
            </section>
        </body>
        </html>
        """
        result = extract_protocol_content(html)
        assert result is not None
        assert "Protocol section content here" in result
    
    def test_extract_from_comment_markers(self):
        """Test extraction from PROTOCOL START/END markers."""
        html = """
        <html>
        <body>
            <!-- PROTOCOL START -->
            Marked protocol content.
            <!-- PROTOCOL END -->
        </body>
        </html>
        """
        result = extract_protocol_content(html)
        assert result is not None
        assert "Marked protocol content" in result
    
    def test_extract_from_pre_tag(self):
        """Test extraction from <pre> tag as fallback."""
        html = """
        <html>
        <body>
            <pre>
                Pre-formatted protocol content.
            </pre>
        </body>
        </html>
        """
        result = extract_protocol_content(html)
        assert result is not None
        assert "Pre-formatted protocol content" in result
    
    def test_fallback_to_text_extraction(self):
        """Test fallback to text extraction when no specific pattern found."""
        html = """
        <html>
        <body>
            <p>Some general content.</p>
            <p>Protocol related text.</p>
        </body>
        </html>
        """
        result = extract_protocol_content(html)
        # Should still return something (all text)
        assert result is not None
        assert "Protocol related text" in result

class TestCleanHtmlTags:
    """Tests for cleaning HTML tags from content."""
    
    def test_remove_simple_tags(self):
        """Test removal of simple HTML tags."""
        content = "<p>Hello <strong>World</strong></p>"
        result = clean_html_tags(content)
        assert result == "Hello World"
    
    def test_remove_nested_tags(self):
        """Test removal of nested HTML tags."""
        content = "<div><p>Text with <em>emphasis</em> and <strong>bold</strong></p></div>"
        result = clean_html_tags(content)
        assert result == "Text with emphasis and bold"
    
    def test_normalize_whitespace(self):
        """Test normalization of whitespace."""
        content = "Line 1\n\n\nLine 2\n\n\n\nLine 3"
        result = clean_html_tags(content)
        # Should normalize multiple newlines
        assert "\n\n\n" not in result
    
    def test_strip_trailing_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        content = "  <p>Content</p>  "
        result = clean_html_tags(content)
        assert result == "Content"
    
    def test_preserve_newlines(self):
        """Test that meaningful newlines are preserved."""
        content = "<p>Line 1</p>\n<p>Line 2</p>"
        result = clean_html_tags(content)
        assert "Line 1" in result
        assert "Line 2" in result

class TestSaveProtocolContent:
    """Tests for saving protocol content to file."""
    
    def test_save_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        output_file = tmp_path / "subdir" / "nested" / "protocol.md"
        content = "Test content"
        
        save_protocol_content(content, str(output_file))
        
        assert output_file.exists()
        assert output_file.read_text() == content
    
    def test_save_with_utf8_encoding(self, tmp_path):
        """Test that content is saved with UTF-8 encoding."""
        output_file = tmp_path / "protocol.md"
        content = "Protocol with unicode: café, naïve, 日本語"
        
        save_protocol_content(content, str(output_file))
        
        # Read back with UTF-8
        result = output_file.read_text(encoding='utf-8')
        assert result == content
    
    def test_save_preserves_content(self, tmp_path):
        """Test that content is preserved exactly."""
        output_file = tmp_path / "protocol.md"
        content = """# Protocol Title

        ## Steps
        1. First step
        2. Second step
        """
        
        save_protocol_content(content, str(output_file))
        
        result = output_file.read_text()
        assert result == content