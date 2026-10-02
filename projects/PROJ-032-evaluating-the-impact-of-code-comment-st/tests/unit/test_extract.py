"""
Unit tests for the extract module.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from extract import extract_comments_ast, extract_comments_from_file, run_extraction_pipeline

class TestExtractCommentsAST:
    def test_extract_simple_comment(self):
        code = "# This is a comment\ndef foo(): pass"
        comments = extract_comments_ast(code)
        assert len(comments) == 1
        assert comments[0]["text"] == "# This is a comment"
        assert comments[0]["start_line"] == 1

    def test_extract_multiple_comments(self):
        code = """
        # Comment 1
        def bar():
            # Comment 2
            pass
        # Comment 3
        """
        comments = extract_comments_ast(code)
        assert len(comments) == 3
        assert "Comment 1" in comments[0]["text"]
        assert "Comment 2" in comments[1]["text"]
        assert "Comment 3" in comments[2]["text"]

    def test_empty_source(self):
        comments = extract_comments_ast("")
        assert len(comments) == 0

    def test_whitespace_only(self):
        comments = extract_comments_ast("   \n\t  ")
        assert len(comments) == 0

    def test_no_comments(self):
        code = "def foo():\n    x = 1\n    return x"
        comments = extract_comments_ast(code)
        assert len(comments) == 0

    def test_invalid_syntax(self):
        # Tree-sitter should handle this gracefully and return empty or partial
        code = "def foo(: # broken syntax"
        # Should not raise an exception
        comments = extract_comments_ast(code)
        # Depending on parser behavior, might be empty or partial, but must not crash
        assert isinstance(comments, list)

class TestExtractCommentsFromFile:
    def test_extract_from_temp_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# Test comment\nx = 1")
            temp_path = f.name

        try:
            comments = extract_comments_from_file(temp_path)
            assert len(comments) == 1
            assert comments[0]["text"] == "# Test comment"
        finally:
            os.unlink(temp_path)

    def test_nonexistent_file(self):
        comments = extract_comments_from_file("nonexistent_file_12345.py")
        assert len(comments) == 0

class TestRunExtractionPipeline:
    def test_pipeline_creates_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy repo structure
            repo_dir = Path(tmpdir) / "repo"
            repo_dir.mkdir()
            file_path = repo_dir / "test.py"
            file_path.write_text("# Hello\nx = 1")
            
            output_file = Path(tmpdir) / "output.json"
            
            run_extraction_pipeline([str(repo_dir)], str(output_file))
            
            assert output_file.exists()
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 1
            assert data[0]["file_path"] == str(file_path)
            assert len(data[0]["comments"]) == 1
            assert data[0]["comments"][0]["text"] == "# Hello"

    def test_pipeline_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "empty_output.json"
            run_extraction_pipeline([tmpdir], str(output_file))
            
            assert output_file.exists()
            with open(output_file, 'r') as f:
                data = json.load(f)
            assert data == []