import pytest
from data.extract_github import parse_git_log_and_count_authors

def test_author_count_calculation():
    """
    Test that the unique author count is calculated correctly from git log output.
    Mock git log output with lines: "Author A", "Author B", "Author A".
    Assert unique author count is 2 (minimal).
    """
    # Mock git log output (simulating 'git log --format="%aN"')
    mock_git_log_output = """
    Author A
    Author B
    Author A
    Author C
    Author B
    """

    # Expected unique authors: Author A, Author B, Author C -> count = 3
    # However, the task description says "Author A", "Author B", "Author A" -> count = 2
    # Let's adjust the mock to match the task description exactly
    mock_git_log_output_simple = """
    Author A
    Author B
    Author A
    """

    unique_authors = parse_git_log_and_count_authors(mock_git_log_output_simple)

    # Assert the unique author count is 2
    assert unique_authors == 2, f"Expected 2 unique authors, got {unique_authors}"
