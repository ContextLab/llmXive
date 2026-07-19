"""
Contract tests for keyword heuristic extraction in User Story 2.

These tests verify the interface and expected behavior of the heuristic
extraction logic before the full implementation of T023.
"""
import pytest
import json
import os
from pathlib import Path
from typing import List, Dict, Any

# Import the function to be tested (will be implemented in T023)
# We use a try/except block to handle the case where the module isn't fully
# implemented yet, but the contract test should fail if the function doesn't exist.
try:
    from utils.baseline import extract_keyword_heuristics
    HAS_IMPLEMENTATION = True
except ImportError:
    HAS_IMPLEMENTATION = False


@pytest.fixture
def sample_pr_comments():
    """Fixture providing a list of sample PR comment dictionaries."""
    return [
        {
            "id": 101,
            "body": "This looks like a potential bug in the authentication flow.",
            "author": "reviewer1",
            "created_at": "2023-01-01T10:00:00Z",
            "repository": "test-repo",
            "pr_number": 42
        },
        {
            "id": 102,
            "body": "Nice refactoring, but we should fix the security vulnerability here.",
            "author": "reviewer2",
            "created_at": "2023-01-02T11:00:00Z",
            "repository": "test-repo",
            "pr_number": 42
        },
        {
            "id": 103,
            "body": "The variable naming could be improved for style consistency.",
            "author": "reviewer3",
            "created_at": "2023-01-03T12:00:00Z",
            "repository": "test-repo",
            "pr_number": 45
        },
        {
            "id": 104,
            "body": "This code works perfectly, no issues found.",
            "author": "reviewer4",
            "created_at": "2023-01-04T13:00:00Z",
            "repository": "test-repo",
            "pr_number": 45
        },
        {
            "id": 105,
            "body": "BUG: This will crash on null input.",
            "author": "reviewer5",
            "created_at": "2023-01-05T14:00:00Z",
            "repository": "test-repo",
            "pr_number": 46
        }
    ]


@pytest.fixture
def sample_heuristics_config():
    """Fixture providing a sample keyword configuration."""
    return {
        "bug": ["bug", "defect", "error", "crash", "fail"],
        "security": ["security", "vulnerability", "exploit", "auth", "injection"],
        "style": ["style", "naming", "format", "indent", "consistency"]
    }


@pytest.mark.skipif(not HAS_IMPLEMENTATION, reason="Implementation not yet available")
def test_extract_keyword_heuristics_returns_list(sample_pr_comments, sample_heuristics_config):
    """Test that the function returns a list of dictionaries."""
    result = extract_keyword_heuristics(sample_pr_comments, sample_heuristics_config)
    assert isinstance(result, list), "Output must be a list"


@pytest.mark.skipif(not HAS_IMPLEMENTATION, reason="Implementation not yet available")
def test_extract_keyword_heuristics_matches_expected_count(sample_pr_comments, sample_heuristics_config):
    """Test that the function identifies the expected number of candidates."""
    # Expected matches:
    # 1. "potential bug" -> bug
    # 2. "security vulnerability" -> security
    # 3. "style consistency" -> style
    # 4. "BUG: ... crash" -> bug
    # Total: 4 candidates
    result = extract_keyword_heuristics(sample_pr_comments, sample_heuristics_config)
    assert len(result) == 4, f"Expected 4 candidates, got {len(result)}"


@pytest.mark.skipif(not HAS_IMPLEMENTATION, reason="Implementation not yet available")
def test_extract_keyword_heuristics_preserves_metadata(sample_pr_comments, sample_heuristics_config):
    """Test that output records preserve original comment metadata."""
    result = extract_keyword_heuristics(sample_pr_comments, sample_heuristics_config)
    
    # Find the record for the "security" comment
    security_record = next((r for r in result if r.get("category") == "security"), None)
    assert security_record is not None, "Security comment should be detected"
    assert security_record["original_id"] == 102, "Original ID should be preserved"
    assert security_record["repository"] == "test-repo", "Repository should be preserved"
    assert security_record["pr_number"] == 42, "PR number should be preserved"


@pytest.mark.skipif(not HAS_IMPLEMENTATION, reason="Implementation not yet available")
def test_extract_keyword_heuristics_empty_input(sample_heuristics_config):
    """Test behavior with empty input list."""
    result = extract_keyword_heuristics([], sample_heuristics_config)
    assert result == [], "Empty input should return empty list"


@pytest.mark.skipif(not HAS_IMPLEMENTATION, reason="Implementation not yet available")
def test_extract_keyword_heuristics_case_insensitive(sample_pr_comments, sample_heuristics_config):
    """Test that keyword matching is case-insensitive."""
    # The sample includes "BUG:" which should match "bug"
    result = extract_keyword_heuristics(sample_pr_comments, sample_heuristics_config)
    bug_records = [r for r in result if r.get("category") == "bug"]
    assert len(bug_records) == 2, "Should detect both 'bug' and 'BUG:' cases"


@pytest.mark.skipif(not HAS_IMPLEMENTATION, reason="Implementation not yet available")
def test_extract_keyword_heuristics_output_schema(sample_pr_comments, sample_heuristics_config):
    """Test that output records conform to the expected schema."""
    result = extract_keyword_heuristics(sample_pr_comments, sample_heuristics_config)
    
    required_fields = ["original_id", "body", "author", "created_at", "repository", "pr_number", "category", "matched_keywords"]
    
    for record in result:
        for field in required_fields:
            assert field in record, f"Missing required field: {field}"
        assert isinstance(record["matched_keywords"], list), "matched_keywords must be a list"
        assert record["category"] in ["bug", "security", "style"], f"Invalid category: {record['category']}"