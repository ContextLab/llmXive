import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the functions to test
from src.templates.fetcher import (
    read_verified_url,
    fetch_url_content,
    extract_protocol_content,
    clean_html_tags,
    save_protocol_content,
    TEMPLATES_DIR,
    VERIFIED_URL_FILE,
    OUTPUT_FILE
)

class TestReadVerifiedUrl:
    def test_read_existing_url(self, tmp_path):
        # Setup: Create a mock file structure
        mock_templates_dir = tmp_path / "templates"
        mock_templates_dir.mkdir()
        mock_url_file = mock_templates_dir / "verified_template_url.txt"
        mock_url_file.write_text("https://example.com/protocol")

        # Mock the global constant to point to our temp dir
        with patch('src.templates.fetcher.VERIFIED_URL_FILE', mock_url_file):
            url = read_verified_url()
            assert url == "https://example.com/protocol"

    def test_missing_file_raises_error(self, tmp_path):
        mock_templates_dir = tmp_path / "templates"
        mock_templates_dir.mkdir()
        mock_url_file = mock_templates_dir / "verified_template_url.txt"

        with patch('src.templates.fetcher.VERIFIED_URL_FILE', mock_url_file):
            with pytest.raises(FileNotFoundError):
                read_verified_url()

    def test_empty_file_raises_error(self, tmp_path):
        mock_templates_dir = tmp_path / "templates"
        mock_templates_dir.mkdir()
        mock_url_file = mock_templates_dir / "verified_template_url.txt"
        mock_url_file.write_text("")

        with patch('src.templates.fetcher.VERIFIED_URL_FILE', mock_url_file):
            with pytest.raises(ValueError):
                read_verified_url()

class TestFetchUrlContent:
    @patch('src.templates.fetcher.requests.get')
    def test_successful_fetch(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        content = fetch_url_content("https://example.com")
        assert content == "<html><body>Content</body></html>"
        mock_get.assert_called_once_with("https://example.com", timeout=30)

    @patch('src.templates.fetcher.requests.get')
    def test_fetch_failure_raises_error(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(RuntimeError, match="Failed to fetch URL"):
            fetch_url_content("https://example.com")

class TestExtractProtocolContent:
    def test_extract_from_protocol_div(self):
        html = """
        <html>
        <body>
            <div class="protocol">
                <p>This is the protocol content.</p>
            </div>
        </body>
        </html>
        """
        extracted = extract_protocol_content(html)
        assert "This is the protocol content." in extracted

    def test_extract_from_protocol_section_header(self):
        html = """
        <html>
        <body>
            <h2>Protocol</h2>
            <p>Steps here.</p>
            <div>Footer</div>
        </body>
        </html>
        """
        extracted = extract_protocol_content(html)
        assert "Steps here." in extracted

    def test_extract_from_body_fallback(self):
        html = """
        <html>
        <body>
            <p>Body content without specific tags.</p>
        </body>
        </html>
        """
        extracted = extract_protocol_content(html)
        assert "Body content without specific tags." in extracted

class TestCleanHtmlTags:
    def test_removes_tags(self):
        html = "<div><p>Hello</p> <span>World</span></div>"
        clean = clean_html_tags(html)
        assert "<" not in clean and ">" not in clean
        assert "Hello" in clean
        assert "World" in clean

    def test_normalizes_whitespace(self):
        html = "<div>  Hello    World  </div>"
        clean = clean_html_tags(html)
        assert "  " not in clean
        assert "Hello World" in clean

class TestSaveProtocolContent:
    def test_saves_to_file(self, tmp_path):
        output_path = tmp_path / "test_output.md"
        content = "Test content"

        save_protocol_content(content, output_path)

        assert output_path.exists()
        assert output_path.read_text() == content
