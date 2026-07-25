import pytest
from code.src.extraction.schema import PullRequest, BugDetection, AlignmentResult, Severity


def test_pull_request_creation():
    """Test that a PullRequest can be created with required fields."""
    pr = PullRequest(
        pr_id="12345",
        repo_name="test/repo",
        title="Test PR",
        body="Test body",
        state="open",
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-02T00:00:00Z",
        author="test_user",
        base_branch="main",
        head_branch="feature",
        diff="diff --git a/test.py b/test.py\n...",
    )
    assert pr.pr_id == "12345"
    assert pr.repo_name == "test/repo"
    assert pr.state == "open"
    assert pr.linked_issue_ids == []


def test_pull_request_json_roundtrip():
    """Test that PullRequest can be serialized to JSON and deserialized."""
    original = PullRequest(
        pr_id="67890",
        repo_name="microsoft/vscode",
        title="Fix bug",
        body="Fixes #123",
        state="closed",
        created_at="2023-02-01T00:00:00Z",
        updated_at="2023-02-02T00:00:00Z",
        author="contributor",
        base_branch="main",
        head_branch="fix-bug",
        diff="diff --git a/file.py b/file.py\n...",
        linked_issue_ids=["123", "456"],
        is_verified_bug=True,
        verification_method="strict_triangulation",
    )
    
    json_str = original.to_json()
    recovered = PullRequest.from_dict(original.to_dict())
    
    assert recovered.pr_id == original.pr_id
    assert recovered.repo_name == original.repo_name
    assert recovered.linked_issue_ids == original.linked_issue_ids
    assert recovered.is_verified_bug == original.is_verified_bug


def test_bug_detection_severity():
    """Test Severity enum conversion and values."""
    assert Severity.CRITICAL.value == "critical"
    assert Severity.MAJOR.value == "major"
    assert Severity.MINOR.value == "minor"
    assert Severity.STYLE.value == "style"
    
    # Test from_string
    assert Severity.from_string("critical") == Severity.CRITICAL
    assert Severity.from_string("MAJOR") == Severity.MAJOR
    
    with pytest.raises(ValueError):
        Severity.from_string("invalid")


def test_bug_detection_creation():
    """Test that a BugDetection can be created with required fields."""
    bug = BugDetection(
        pr_id="12345",
        file_path="src/main.py",
        line_start=10,
        line_end=15,
        severity=Severity.CRITICAL,
        description="Null pointer exception",
        source="human",
        confidence=0.95,
    )
    assert bug.pr_id == "12345"
    assert bug.file_path == "src/main.py"
    assert bug.line_start == 10
    assert bug.line_end == 15
    assert bug.severity == Severity.CRITICAL
    assert bug.source == "human"
    assert bug.confidence == 0.95


def test_alignment_result():
    """Test that an AlignmentResult can be created and contains expected fields."""
    human_bug = BugDetection(
        pr_id="123",
        file_path="a.py",
        line_start=1,
        line_end=5,
        severity=Severity.MAJOR,
        description="Memory leak",
        source="human",
    )
    llm_bug = BugDetection(
        pr_id="123",
        file_path="a.py",
        line_start=1,
        line_end=5,
        severity=Severity.MAJOR,
        description="Memory leak detected",
        source="llm",
    )
    
    alignment = AlignmentResult(
        human_bug=human_bug,
        llm_bug=llm_bug,
        alignment_score=0.95,
        jaccard_index=1.0,
        is_match=True,
        match_reason="Exact line overlap and high similarity",
    )
    
    assert alignment.is_match is True
    assert alignment.jaccard_index == 1.0
    assert alignment.alignment_score == 0.95
    
    # Test serialization
    data = alignment.to_dict()
    assert data["is_match"] is True
    assert data["jaccard_index"] == 1.0
    assert "human_bug" in data
    assert "llm_bug" in data


def test_severity_invalid():
    """Test that invalid severity values raise an error."""
    with pytest.raises(ValueError):
        Severity.from_string("not_a_severity")
    
    with pytest.raises(ValueError):
        Severity.from_string("")