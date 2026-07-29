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
    fetch_url_content,
    extract_protocol_content,
    clean_html_tags,
    save_protocol_content
)

class TestReadVerifiedUrl:
    def test_read_existing_file(self, tmp_path):
        url_file = tmp_path / "verified_url.txt"
        test_url = "https://example.com/protocol"
        url_file.write_text(test_url)
        
        result = read_verified_url(str(url_file))
        assert result == test_url

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_verified_url(str(tmp_path / "nonexistent.txt"))

    def test_empty_file(self, tmp_path):
        url_file = tmp_path / "empty.txt"
        url_file.write_text("")
        
        with pytest.raises(ValueError, match="Verified URL file is empty"):
            read_verified_url(str(url_file))

class TestExtractProtocolContent:
    def test_extract_div_protocol(self):
        html = """
        <html>
        <body>
            <div class="protocol">
                <h2>Step 1</h2>
                <p>Prepare the solution.</p>
            </div>
        </body>
        </html>
        """
        result = extract_protocol_content(html)
        assert "<h2>Step 1</h2>" in result
        assert "Prepare the solution" in result

    def test_extract_section_protocol(self):
        html = """
        <html>
        <body>
            <section class="protocol">
                <p>Methodology details.</p>
            </section>
        </body>
        </html>
        """
        result = extract_protocol_content(html)
        assert "Methodology details" in result

    def test_extract_header_protocol(self):
        html = """
        <html>
        <body>
            <h2>Protocol</h2>
            <p>Instruction text.</p>
            <p>More text.</p>
        </body>
        </html>
        """
        result = extract_protocol_content(html)
        assert "Instruction text" in result
        assert "More text" in result

    def test_fallback_to_body(self):
        html = """
        <html>
        <body>
            <p>Generic content.</p>
        </body>
        </html>
        """
        result = extract_protocol_content(html)
        assert "Generic content" in result

class TestCleanHtmlTags:
    def test_remove_simple_tags(self):
        text = "<p>Hello <b>World</b></p>"
        result = clean_html_tags(text)
        assert "Hello" in result
        assert "World" in result
        assert "<" not in result

    def test_remove_script_tags(self):
        text = "<p>Text</p><script>alert('bad');</script><p>More</p>"
        result = clean_html_tags(text)
        assert "alert" not in result
        assert "Text" in result
        assert "More" in result

    def test_decode_entities(self):
        text = "A &amp; B &lt; C &gt; D"
        result = clean_html_tags(text)
        assert "A & B < C > D" in result

    def test_normalize_whitespace(self):
        text = "  Hello   World  "
        result = clean_html_tags(text)
        assert result == "Hello World"

class TestSaveProtocolContent:
    def test_save_creates_file(self, tmp_path):
        content = "# Test Protocol\n\nStep 1: Do something."
        output_file = tmp_path / "output.md"
        
        save_protocol_content(content, str(output_file))
        
        assert output_file.exists()
        assert output_file.read_text() == content

    def test_save_creates_directories(self, tmp_path):
        content = "Content"
        nested_file = tmp_path / "sub" / "dir" / "output.md"
        
        save_protocol_content(content, str(nested_file))
        
        assert nested_file.exists()
        assert nested_file.read_text() == content
