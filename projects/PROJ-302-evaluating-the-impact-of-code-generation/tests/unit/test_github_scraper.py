import pytest
from datetime import datetime
from code.data_acquisition.github_scraper import parse_iso_date, parse_pr_response, parse_file_content

def test_parse_iso_date_valid():
    """Test parsing valid ISO 8601 strings."""
    assert parse_iso_date("2023-10-01T12:00:00Z") is not None
    assert parse_iso_date("2023-10-01T12:00:00+00:00") is not None
    assert parse_iso_date("2023-10-01T12:00:00") is not None

def test_parse_iso_date_invalid():
    """Test handling of invalid date strings."""
    assert parse_iso_date("not-a-date") is None
    assert parse_iso_date(None) is None
    assert parse_iso_date("") is None

def test_parse_pr_response_minimal():
    """Test parsing a minimal PR response."""
    pr_data = {
        "number": 123,
        "state": "closed",
        "created_at": "2023-01-01T00:00:00Z",
        "user": {"login": "test_user"},
        "base": {"repo": {"id": 1, "full_name": "test/repo"}},
        "head": {"repo": {"full_name": "test/repo"}},
        "additions": 10,
        "deletions": 5,
        "changed_files": 2,
        "title": "Test PR",
        "body": "Test body",
        "labels": []
    }
    pr = parse_pr_response(pr_data)
    assert pr.pr_id == "123"
    assert pr.repo_id == "1"
    assert pr.author_type == "human"
    assert pr.state == "closed"
    assert pr.additions == 10
    assert pr.title == "Test PR"

def test_parse_pr_response_bot_detection():
    """Test that bot users are correctly identified."""
    pr_data = {
        "number": 1,
        "state": "open",
        "user": {"login": "dependabot[bot]"},
        "base": {"repo": {"id": 999, "full_name": "org/repo"}},
        "head": {"repo": {"full_name": "org/repo"}}
    }
    pr = parse_pr_response(pr_data)
    assert pr.author_type == "bot"

def test_parse_file_content_base64():
    """Test parsing file content with base64 encoding."""
    import base64
    raw_content = "def hello():\n    pass"
    encoded = base64.b64encode(raw_content.encode('utf-8')).decode('utf-8')
    
    file_data = {
        "sha": "abc123",
        "filename": "test.py",
        "encoding": "base64",
        "content": encoded,
        "language": "Python"
    }
    
    snippet = parse_file_content(file_data)
    assert snippet.content == raw_content
    assert snippet.size_bytes == len(raw_content.encode('utf-8'))
    assert snippet.language == "Python"

def test_parse_file_content_raw():
    """Test parsing file content with raw encoding."""
    file_data = {
        "sha": "def456",
        "filename": "script.py",
        "encoding": "utf-8",
        "content": "print('hello')",
        "language": "Python"
    }
    
    snippet = parse_file_content(file_data)
    assert snippet.content == "print('hello')"
    assert snippet.filename == "script.py"
