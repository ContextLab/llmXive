import pytest
import json
import os
import tempfile
from pathlib import Path
from extract import extract_comments_ast, extract_comments_from_file, run_extraction_pipeline

def test_extract_comments_ast_basic():
    """Test extraction of simple comments."""
    source = """
    # This is a comment
    x = 1
    # Another comment
    def foo():
        pass
    """
    comments = extract_comments_ast(source)
    assert len(comments) == 2
    assert "# This is a comment" in comments[0]["text"]
    assert "# Another comment" in comments[1]["text"]

def test_extract_comments_ast_no_comments():
    """Test extraction when no comments exist."""
    source = """
    x = 1
    y = 2
    def foo():
        return x + y
    """
    comments = extract_comments_ast(source)
    assert len(comments) == 0

def test_extract_comments_ast_empty_file():
    """Test extraction on empty source."""
    comments = extract_comments_ast("")
    assert len(comments) == 0

def test_extract_comments_ast_string_literals_ignored():
    """Test that string literals are not treated as comments."""
    source = """
    x = "# This is not a comment"
    y = 'Also not a comment'
    # This is a real comment
    """
    comments = extract_comments_ast(source)
    assert len(comments) == 1
    assert "# This is a real comment" in comments[0]["text"]

def test_extract_comments_ast_syntax_error_handling():
    """Test graceful handling of syntax errors."""
    source = """
    def broken(
        # Missing closing paren
    x = 1
    """
    # Should not raise an exception, just return empty or partial
    comments = extract_comments_ast(source)
    # Depending on tree-sitter behavior, it might parse what it can or return empty.
    # We just assert it didn't crash.
    assert isinstance(comments, list)

def test_extract_comments_from_file(tmp_path):
    """Test extraction from a temporary file."""
    test_file = tmp_path / "test.py"
    content = """
    # File comment
    x = 1
    """
    test_file.write_text(content)
    
    comments = extract_comments_from_file(str(test_file))
    assert len(comments) == 1
    assert "# File comment" in comments[0]["text"]

def test_run_extraction_pipeline(tmp_path):
    """Test the full pipeline on a directory of files."""
    # Create test directory with Python files
    test_dir = tmp_path / "test_repos"
    test_dir.mkdir()
    
    file1 = test_dir / "file1.py"
    file1.write_text("# Comment 1\nx = 1")
    
    file2 = test_dir / "subdir" / "file2.py"
    file2.parent.mkdir()
    file2.write_text("# Comment 2\ny = 2")
    
    output_path = tmp_path / "output.json"
    
    run_extraction_pipeline(str(test_dir), str(output_path))
    
    assert output_path.exists()
    with open(output_path, "r") as f:
        data = json.load(f)
    
    assert len(data) == 2
    # Check that comments were found in both files
    found_comments = sum(len(item["comments"]) for item in data)
    assert found_comments == 2