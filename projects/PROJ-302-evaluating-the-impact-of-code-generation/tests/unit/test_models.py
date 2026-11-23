import pytest
from datetime import datetime
from utils.models import PullRequest, CodeSnippet

def test_pull_request_creation():
    """Test PullRequest dataclass instantiation."""
    pr = PullRequest(
        pr_id="PR-123",
        repo_id="repo-456",
        author_type="human",
        review_duration=3600,
        file_size=1024,
        complexity_score=5.0
    )
    
    assert pr.pr_id == "PR-123"
    assert pr.repo_id == "repo-456"
    assert pr.author_type == "human"
    assert pr.review_duration == 3600
    assert pr.file_size == 1024
    assert pr.complexity_score == 5.0

def test_pull_request_default_values():
    """Test PullRequest with default values."""
    pr = PullRequest(pr_id="PR-123", repo_id="repo-456")
    
    assert pr.author_type is None
    assert pr.review_duration is None
    assert pr.file_size is None
    assert pr.complexity_score is None

def test_code_snippet_creation():
    """Test CodeSnippet dataclass instantiation."""
    snippet = CodeSnippet(
        snippet_id="SNIP-001",
        source_commit="abc123",
        generation_source="human",
        complexity_metrics={"cyclomatic": 3},
        semantic_similarity_score=0.85
    )
    
    assert snippet.snippet_id == "SNIP-001"
    assert snippet.source_commit == "abc123"
    assert snippet.generation_source == "human"
    assert snippet.complexity_metrics == {"cyclomatic": 3}
    assert snippet.semantic_similarity_score == 0.85

def test_code_snippet_json_serialization():
    """Test CodeSnippet can be serialized to JSON."""
    snippet = CodeSnippet(
        snippet_id="SNIP-001",
        source_commit="abc123",
        generation_source="human"
    )
    
    json_str = snippet.to_json()
    assert isinstance(json_str, str)
    assert "SNIP-001" in json_str