import os
import csv
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from utils import validate_tools_and_log, get_logger

@pytest.fixture
def mock_repos_csv(tmp_path):
    """Create a temporary CSV with mock repo data."""
    csv_path = tmp_path / "repos_metadata.csv"
    data = [
        {"owner": "test", "repo_name": "repo_high_stars", "stars": "6000", "citation": ""},
        {"owner": "test", "repo_name": "repo_low_stars_cited", "stars": "1000", "citation": "Smith et al. 2020"},
        {"owner": "test", "repo_name": "repo_low_stars_no_cite", "stars": "100", "citation": ""},
    ]
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["owner", "repo_name", "stars", "citation"])
        writer.writeheader()
        writer.writerows(data)
    return str(csv_path)

@patch('utils.requests.get')
def test_validate_tools_and_log(mock_get, mock_repos_csv, tmp_path):
    """Test that validate_tools_and_log correctly fetches stars and determines status."""
    # Mock GitHub API responses
    mock_response_high = MagicMock()
    mock_response_high.json.return_value = {"stargazers_count": 6000}
    mock_response_high.raise_for_status.return_value = None

    mock_response_low = MagicMock()
    mock_response_low.json.return_value = {"stargazers_count": 1000}
    mock_response_low.raise_for_status.return_value = None

    mock_response_fail = MagicMock()
    mock_response_fail.json.return_value = {"stargazers_count": 100}
    mock_response_fail.raise_for_status.return_value = None

    # Map repo names to responses
    def side_effect(url, *args, **kwargs):
        if "repo_high_stars" in url:
            return mock_response_high
        elif "repo_low_stars_cited" in url:
            return mock_response_low
        elif "repo_low_stars_no_cite" in url:
            return mock_response_fail
        return MagicMock() # Default

    mock_get.side_effect = side_effect

    log_path = tmp_path / "tool_validation_log.csv"
    
    # Run the function
    validate_tools_and_log(mock_repos_csv, str(log_path))

    # Verify output file exists
    assert log_path.exists()

    # Verify content
    with open(log_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # We have 3 repos * 2 tools (radon, semgrep) = 6 rows
    assert len(rows) == 6

    # Check specific statuses
    # repo_high_stars: stars > 5000 -> PASS
    high_star_rows = [r for r in rows if "repo_high_stars" in r['repo']]
    assert all(r['status'] == 'PASS' for r in high_star_rows)
    assert all(r['stars'] == '6000' for r in high_star_rows)

    # repo_low_stars_cited: stars <= 5000 but citation present -> PASS
    cited_rows = [r for r in rows if "repo_low_stars_cited" in r['repo']]
    assert all(r['status'] == 'PASS' for r in cited_rows)
    assert all(r['stars'] == '1000' for r in cited_rows)

    # repo_low_stars_no_cite: stars <= 5000 and no citation -> FAIL
    no_cite_rows = [r for r in rows if "repo_low_stars_no_cite" in r['repo']]
    assert all(r['status'] == 'FAIL' for r in no_cite_rows)
    assert all(r['stars'] == '100' for r in no_cite_rows)

    # Verify tool names and versions
    tools = set()
    for r in rows:
        tools.add((r['tool_name'], r['version']))
    
    assert ('radon', '2.4.0') in tools
    assert ('semgrep', '1.30.0') in tools