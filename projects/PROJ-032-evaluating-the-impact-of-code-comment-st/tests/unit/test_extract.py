import pytest
import os
import json
import tempfile
from pathlib import Path
import sys

# Add code directory to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from extract import extract_comments_ast, extract_comments_from_file, extract_comments_batch

class TestExtractCommentsAST:
    def test_simple_comment(self):
        code = """
        # This is a comment
        x = 1
        """
        comments = extract_comments_ast(code)
        assert len(comments) == 1
        assert "This is a comment" in comments[0]["text"]
        assert comments[0]["start_line"] == 2

    def test_multiple_comments(self):
        code = """
        # Comment 1
        def foo():
            # Comment 2
            pass
        """
        comments = extract_comments_ast(code)
        assert len(comments) == 2
        assert "Comment 1" in comments[0]["text"]
        assert "Comment 2" in comments[1]["text"]

    def test_empty_code(self):
        code = ""
        comments = extract_comments_ast(code)
        assert len(comments) == 0

    def test_no_comments(self):
        code = """
        x = 1
        y = 2
        """
        comments = extract_comments_ast(code)
        assert len(comments) == 0

    def test_syntax_error_handling(self):
        # Invalid Python syntax
        code = """
        def foo(
            # Missing closing paren
        """
        # Should not raise, return empty list
        comments = extract_comments_ast(code)
        assert isinstance(comments, list)

class TestExtractCommentsFromFile:
    def test_extract_from_temp_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# Test comment\nx = 1")
            temp_path = f.name

        try:
            comments = extract_comments_from_file(temp_path)
            assert len(comments) == 1
            assert "Test comment" in comments[0]["text"]
        finally:
            os.unlink(temp_path)

    def test_nonexistent_file(self):
        comments = extract_comments_from_file("/nonexistent/file.py")
        assert len(comments) == 0

class TestExtractCommentsBatch:
    def test_batch_extraction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two test files
            file1 = Path(tmpdir) / "file1.py"
            file2 = Path(tmpdir) / "file2.py"
            
            file1.write_text("# Comment 1\nx = 1")
            file2.write_text("# Comment 2\ny = 2")
            
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()
            
            output_file = output_dir / "comments.json"
            
            count = extract_comments_batch([str(file1), str(file2)], str(output_dir))
            
            assert count == 2
            assert output_file.exists()
            
            with open(output_file) as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert any("Comment 1" in c["text"] for c in data)
            assert any("Comment 2" in c["text"] for c in data)
            assert all("source_file" in c for c in data)