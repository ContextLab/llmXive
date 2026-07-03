import subprocess
from unittest.mock import patch, MagicMock
import pytest

from code.data.extract_github import parse_git_log

def test_author_count_calculation():
    """Mock git log output, assert unique author count matches expected."""
    # Simulate git log output with known authors
    mock_git_log_output = """
    commit abc123
    Author: Alice <alice@example.com>
    Date: 2023-01-01
    
        First commit

    commit def456
    Author: Bob <bob@example.com>
    Date: 2023-01-02
    
        Second commit

    commit ghi789
    Author: Alice <alice@example.com>
    Date: 2023-01-03
    
        Third commit

    commit jkl012
    Author: Charlie <charlie@example.com>
    Date: 2023-01-04
    
        Fourth commit
    """

    # Mock the subprocess.run to return our simulated output
    mock_result = MagicMock()
    mock_result.stdout = mock_git_log_output
    mock_result.stderr = ""
    mock_result.returncode = 0

    with patch('code.data.extract_github.run_command', return_value=mock_result):
        # Call the function with a mock repo path
        authors = parse_git_log("/fake/repo/path")
        
        # Assert unique author count
        assert len(authors) == 3, f"Expected 3 unique authors, got {len(authors)}"
        assert "Alice" in authors, "Alice should be in authors"
        assert "Bob" in authors, "Bob should be in authors"
        assert "Charlie" in authors, "Charlie should be in authors"

def test_parse_git_log_empty_output():
    """Test parsing when git log returns no commits."""
    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_result.stderr = ""
    mock_result.returncode = 0

    with patch('code.data.extract_github.run_command', return_value=mock_result):
        authors = parse_git_log("/fake/repo/path")
        assert len(authors) == 0, "Should return empty list for no commits"
