"""
Contract tests for keyword heuristic extraction in the human baseline module.

These tests verify the interface and behavior of the keyword heuristic extraction
logic used to identify potential defect annotations in PR comments.

The tests are designed to fail initially if the implementation is missing or
incorrect, ensuring TDD compliance.
"""
import pytest
import json
import os
from pathlib import Path
from typing import List, Dict, Any

# Import the function to be tested from the baseline module
# Note: We assume the function 'extract_keyword_heuristics' will be implemented
# in code/02_human_baseline.py or a dedicated heuristics module.
# For this contract test, we will import it. If it doesn't exist yet, 
# the test runner will fail with ImportError, which is the expected initial state.
try:
    from utils.heuristics import extract_keyword_heuristics
except ImportError:
    # Fallback if the module structure is slightly different or not yet created
    # In a real TDD flow, we would create the module first.
    # Here we define a stub to allow the test file to load, 
    # but the tests will fail because the logic is missing.
    def extract_keyword_heuristics(comments: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Stub implementation for contract testing."""
        raise NotImplementedError("extract_keyword_heuristics is not implemented yet.")

# --- Fixtures / Sample Data ---

@pytest.fixture
def sample_pr_comments():
    """
    Returns a list of sample PR comments simulating real data structure.
    Schema: {comment_id, text, file, line, timestamp, repo_id}
    """
    return [
        {
            "comment_id": "c001",
            "text": "This looks like a potential bug in the calculation logic.",
            "file": "src/math_utils.py",
            "line": 42,
            "timestamp": "2023-10-01T10:00:00Z",
            "repo_id": "repo-123"
        },
        {
            "comment_id": "c002",
            "text": "Security vulnerability: hardcoded API key detected here.",
            "file": "config/settings.py",
            "line": 15,
            "timestamp": "2023-10-01T11:30:00Z",
            "repo_id": "repo-123"
        },
        {
            "comment_id": "c003",
            "text": "Nice work on the refactoring, but the style could be improved.",
            "file": "src/utils.py",
            "line": 88,
            "timestamp": "2023-10-01T12:00:00Z",
            "repo_id": "repo-123"
        },
        {
            "comment_id": "c004",
            "text": "This is just a question about the architecture.",
            "file": "README.md",
            "line": 5,
            "timestamp": "2023-10-01T12:15:00Z",
            "repo_id": "repo-123"
        },
        {
            "comment_id": "c005",
            "text": "BUG: The loop never terminates if input is empty.",
            "file": "src/processor.py",
            "line": 102,
            "timestamp": "2023-10-01T13:00:00Z",
            "repo_id": "repo-456"
        }
    ]

@pytest.fixture
def sample_heuristics_config():
    """
    Returns the configuration for keyword heuristics.
    Defines keywords for different defect types (bug, security, style).
    """
    return {
        "keywords": {
            "bug": ["bug", "error", "fail", "crash", "issue", "fix", "broken"],
            "security": ["security", "vulnerability", "hack", "leak", "exposed", "insecure"],
            "style": ["style", "format", "naming", "convention", "refactor", "clean"]
        },
        "threshold": 1,  # Minimum keyword matches to flag
        "case_sensitive": False
    }

# --- Contract Tests ---

def test_extract_keyword_heuristics_returns_list(sample_pr_comments, sample_heuristics_config):
    """
    Contract: The function must return a list of dictionaries.
    """
    result = extract_keyword_heuristics(sample_pr_comments, sample_heuristics_config)
    assert isinstance(result, list), "Output must be a list."
    assert all(isinstance(item, dict) for item in result), "Every item in the list must be a dictionary."

def test_extract_keyword_heuristics_matches_expected_count(sample_pr_comments, sample_heuristics_config):
    """
    Contract: With the given sample data and config, we expect exactly 3 matches:
    - c001 (bug)
    - c002 (security)
    - c003 (style)
    - c004 (no match)
    - c005 (bug) -> Wait, c005 also matches 'bug'. So total 4 matches.
    
    Let's re-verify:
    c001: "bug" -> match
    c002: "security", "vulnerability" -> match
    c003: "style" -> match
    c004: no keywords -> no match
    c005: "BUG" -> match (case insensitive)
    
    Total expected: 4
    """
    result = extract_keyword_heuristics(sample_pr_comments, sample_heuristics_config)
    # Assert that we get the expected number of candidates
    assert len(result) == 4, f"Expected 4 heuristic candidates, got {len(result)}"

def test_extract_keyword_heuristics_preserves_metadata(sample_pr_comments, sample_heuristics_config):
    """
    Contract: The output items must preserve the original comment metadata (id, file, line).
    """
    result = extract_keyword_heuristics(sample_pr_comments, sample_heuristics_config)
    
    # Find the result for c001
    c001_result = next((item for item in result if item['comment_id'] == 'c001'), None)
    assert c001_result is not None, "c001 should be in results"
    assert c001_result['file'] == "src/math_utils.py", "File path must be preserved"
    assert c001_result['line'] == 42, "Line number must be preserved"
    assert c001_result['repo_id'] == "repo-123", "Repo ID must be preserved"

def test_extract_keyword_heuristics_empty_input(sample_heuristics_config):
    """
    Contract: Empty input list must return empty output list.
    """
    result = extract_keyword_heuristics([], sample_heuristics_config)
    assert result == [], "Empty input should yield empty output"

def test_extract_keyword_heuristics_case_insensitive(sample_pr_comments, sample_heuristics_config):
    """
    Contract: Keyword matching must be case-insensitive by default.
    'BUG' in c005 should match 'bug' in config.
    """
    # Ensure config says case insensitive
    assert not sample_heuristics_config.get('case_sensitive', False), "Config should be case insensitive"
    
    result = extract_keyword_heuristics(sample_pr_comments, sample_heuristics_config)
    c005_result = next((item for item in result if item['comment_id'] == 'c005'), None)
    assert c005_result is not None, "c005 (with 'BUG') should be detected as a bug"
    assert c005_result['predicted_type'] == 'bug', "Should be classified as 'bug'"

def test_extract_keyword_heuristics_output_schema(sample_pr_comments, sample_heuristics_config):
    """
    Contract: Each output item must have the schema:
    {comment_id, text, predicted_type, file, line}
    """
    result = extract_keyword_heuristics(sample_pr_comments, sample_heuristics_config)
    
    required_keys = {'comment_id', 'text', 'predicted_type', 'file', 'line'}
    
    for item in result:
        assert required_keys.issubset(item.keys()), f"Item missing required keys. Got: {item.keys()}"
        assert 'predicted_type' in item, "predicted_type is mandatory"
        assert item['predicted_type'] in ['bug', 'security', 'style'], f"Invalid predicted_type: {item['predicted_type']}"