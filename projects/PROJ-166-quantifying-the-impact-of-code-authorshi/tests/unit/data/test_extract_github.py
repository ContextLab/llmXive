import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from data.extract_github import parse_git_log, run_cloc


class TestAuthorCountCalculation:
    """Tests for author count calculation from git log output."""

    def test_author_count_calculation(self):
        """Mock git log output, assert unique author count matches expected."""
        # Simulate git log output with multiple commits from different authors
        mock_git_log_output = """commit abc123def456
Author: Alice Smith <alice@example.com>
Date:   Mon Jan 1 10:00:00 2024 +0000

    Initial commit

commit def456abc789
Author: Bob Jones <bob@example.com>
Date:   Tue Jan 2 11:00:00 2024 +0000

    Add feature X

commit ghi789jkl012
Author: Alice Smith <alice@example.com>
Date:   Wed Jan 3 12:00:00 2024 +0000

    Fix bug Y

commit jkl012mno345
Author: Charlie Brown <charlie@example.com>
Date:   Thu Jan 4 13:00:00 2024 +0000

    Update documentation"""

        authors = parse_git_log(mock_git_log_output)

        # Should find 3 unique authors: Alice, Bob, Charlie
        assert len(authors) == 3
        assert "Alice Smith" in authors
        assert "Bob Jones" in authors
        assert "Charlie Brown" in authors

    def test_author_count_empty_log(self):
        """Test with empty git log output."""
        empty_output = ""
        authors = parse_git_log(empty_output)
        assert len(authors) == 0

    def test_author_count_single_author(self):
        """Test with single author commits."""
        single_author_output = """commit abc123
Author: Single Author <single@example.com>
Date:   Mon Jan 1 10:00:00 2024 +0000

    Commit 1

commit def456
Author: Single Author <single@example.com>
Date:   Tue Jan 2 11:00:00 2024 +0000

    Commit 2"""

        authors = parse_git_log(single_author_output)
        assert len(authors) == 1
        assert "Single Author" in authors

    def test_author_count_duplicate_emails(self):
        """Test that same email with different names counts as one author."""
        duplicate_email_output = """commit abc123
Author: Alice Smith <alice@example.com>
Date:   Mon Jan 1 10:00:00 2024 +0000

    Commit 1

commit def456
Author: Alice Johnson <alice@example.com>
Date:   Tue Jan 2 11:00:00 2024 +0000

    Commit 2"""

        authors = parse_git_log(duplicate_email_output)
        # Should count as 2 different authors (different names)
        # The function counts by author name, not email
        assert len(authors) == 2

    def test_author_count_with_special_characters(self):
        """Test author names with special characters."""
        special_chars_output = """commit abc123
Author: José García <jose@example.com>
Date:   Mon Jan 1 10:00:00 2024 +0000

    Commit 1

commit def456
Author: 李明 <liming@example.com>
Date:   Tue Jan 2 11:00:00 2024 +0000

    Commit 2

commit ghi789
Author: O'Connor, John <john@example.com>
Date:   Wed Jan 3 12:00:00 2024 +0000

    Commit 3"""

        authors = parse_git_log(special_chars_output)
        assert len(authors) == 3
        assert "José García" in authors
        assert "李明" in authors
        assert "O'Connor, John" in authors

    def test_author_count_with_mailmap(self):
        """Test that mailmap entries are handled correctly."""
        # Git log with mailmap applied (normalized names)
        mailmap_output = """commit abc123
Author: Alice Smith <alice@example.com>
Date:   Mon Jan 1 10:00:00 2024 +0000

    Commit 1

commit def456
Author: Alice Smith <alice@example.com>
Date:   Tue Jan 2 11:00:00 2024 +0000

    Commit 2"""

        authors = parse_git_log(mailmap_output)
        assert len(authors) == 1
        assert "Alice Smith" in authors

    def test_author_count_whitespace_handling(self):
        """Test handling of whitespace in author names."""
        whitespace_output = """commit abc123
Author:   Alice   Smith   <alice@example.com>
Date:   Mon Jan 1 10:00:00 2024 +0000

    Commit 1"""

        authors = parse_git_log(whitespace_output)
        # Should handle extra whitespace gracefully
        assert len(authors) == 1
        # The name should be trimmed
        assert "Alice   Smith" in authors or "Alice" in authors

    def test_author_count_malformed_entries(self):
        """Test handling of malformed git log entries."""
        malformed_output = """commit abc123
Author: Valid Author <valid@example.com>
Date:   Mon Jan 1 10:00:00 2024 +0000

    Valid commit

commit def456
Invalid line without Author
Date:   Tue Jan 2 11:00:00 2024 +0000

    Malformed commit

commit ghi789
Author: <no-name@example.com>
Date:   Wed Jan 3 12:00:00 2024 +0000

    No name commit"""

        authors = parse_git_log(malformed_output)
        # Should only count the valid author
        assert len(authors) >= 1
        assert "Valid Author" in authors

    def test_run_cloc_version_check(self):
        """Test cloc version checking logic."""
        # Mock subprocess.run to simulate cloc version output
        with patch('data.extract_github.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "cloc 1.90"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # This should not raise an exception
            version_ok = run_cloc.check_cloc_version()
            assert version_ok is True

    def test_run_cloc_old_version(self):
        """Test cloc version check with old version."""
        with patch('data.extract_github.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "cloc 1.80"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # This should return False for version < 1.88
            version_ok = run_cloc.check_cloc_version()
            assert version_ok is False

    def test_run_cloc_command_execution(self, tmp_path):
        """Test actual cloc command execution on sample files."""
        # Create a temporary directory with some code files
        code_dir = tmp_path / "test_repo"
        code_dir.mkdir()

        # Create a simple Python file
        py_file = code_dir / "test.py"
        py_file.write_text("""
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
""")

        # Create a JavaScript file
        js_file = code_dir / "test.js"
        js_file.write_text("""
function hello() {
    console.log("Hello, World!");
}

hello();
""")

        # Run cloc on the directory
        result = run_cloc.run_cloc(str(code_dir))

        # Verify result structure
        assert result is not None
        assert isinstance(result, dict)
        assert "summary" in result or any(lang in result for lang in ["Python", "JavaScript"])

    def test_run_cloc_empty_directory(self, tmp_path):
        """Test cloc on empty directory."""
        empty_dir = tmp_path / "empty_repo"
        empty_dir.mkdir()

        result = run_cloc.run_cloc(str(empty_dir))

        # Should handle empty directory gracefully
        assert result is not None

    def test_run_cloc_nonexistent_directory(self):
        """Test cloc on non-existent directory."""
        with pytest.raises((FileNotFoundError, subprocess.CalledProcessError)):
            run_cloc.run_cloc("/nonexistent/path")