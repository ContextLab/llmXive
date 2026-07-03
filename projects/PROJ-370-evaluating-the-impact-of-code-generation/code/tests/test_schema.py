"""
Unit tests for extraction schema classes.
"""
import pytest
from code.src.extraction.schema import PullRequest, BugDetection, AlignmentResult, Severity


def test_pull_request_creation():
    """Test basic PullRequest creation."""
    pr = PullRequest(
        pr_id="test/repo#1",
        repo="test/repo",
        number=1,
        title="Test PR",
        body="Test body",
        author="testuser"
    )
    assert pr.pr_id == "test/repo#1"
    assert pr.repo == "test/repo"
    assert pr.number == 1
    assert pr.title == "Test PR"
    assert pr.body == "Test body"
    assert pr.author == "testuser"
    assert pr.diff is None
    assert pr.files_changed == []
    assert pr.review_comments == []
    assert pr.linked_issue_ids == []
    assert pr.llm_code_flag is None


def test_pull_request_json_roundtrip():
    """Test PullRequest JSON serialization and deserialization."""
    pr = PullRequest(
        pr_id="test/repo#123",
        repo="test/repo",
        number=123,
        title="Test PR",
        body="Test body",
        author="testuser",
        created_at="2024-01-01T00:00:00Z",
        state="merged",
        diff="@@ -1,3 +1,4 @@\n+new line\n",
        files_changed=["file1.py", "file2.py"],
        review_comments=[{"id": 1, "body": "LGTM"}],
        linked_issue_ids=[456, 789],
        llm_code_flag=True
    )
    
    json_str = pr.to_json()
    assert "test/repo#123" in json_str
    assert "Test PR" in json_str
    
    pr_dict = pr.to_dict()
    pr_restored = PullRequest.from_dict(pr_dict)
    
    assert pr_restored.pr_id == pr.pr_id
    assert pr_restored.repo == pr.repo
    assert pr_restored.number == pr.number
    assert pr_restored.title == pr.title
    assert pr_restored.body == pr.body
    assert pr_restored.author == pr.author
    assert pr_restored.diff == pr.diff
    assert pr_restored.files_changed == pr.files_changed
    assert pr_restored.review_comments == pr.review_comments
    assert pr_restored.linked_issue_ids == pr.linked_issue_ids
    assert pr_restored.llm_code_flag == pr.llm_code_flag


def test_bug_detection_severity():
    """Test Severity enum functionality."""
    assert str(Severity.CRITICAL) == "critical"
    assert str(Severity.MAJOR) == "major"
    assert str(Severity.MINOR) == "minor"
    assert str(Severity.STYLE) == "style"
    
    assert Severity.from_string("critical") == Severity.CRITICAL
    assert Severity.from_string("CRITICAL") == Severity.CRITICAL
    assert Severity.from_string("major") == Severity.MAJOR
    assert Severity.from_string("Minor") == Severity.MINOR
    
    with pytest.raises(ValueError):
        Severity.from_string("invalid")


def test_bug_detection_creation():
    """Test BugDetection creation and serialization."""
    bug = BugDetection(
        pr_id="test/repo#1",
        file_path="src/main.py",
        line_start=10,
        line_end=15,
        severity=Severity.CRITICAL,
        description="Null pointer exception",
        source="human",
        is_verified=True,
        verification_method="strict_triangulation"
    )
    
    assert bug.pr_id == "test/repo#1"
    assert bug.file_path == "src/main.py"
    assert bug.line_start == 10
    assert bug.line_end == 15
    assert bug.severity == Severity.CRITICAL
    assert bug.description == "Null pointer exception"
    assert bug.source == "human"
    assert bug.is_verified is True
    assert bug.verification_method == "strict_triangulation"
    
    bug_dict = bug.to_dict()
    assert bug_dict["severity"] == "critical"
    
    bug_restored = BugDetection.from_dict(bug_dict)
    assert bug_restored.pr_id == bug.pr_id
    assert bug_restored.severity == Severity.CRITICAL


def test_alignment_result():
    """Test AlignmentResult creation and serialization."""
    alignment = AlignmentResult(
        llm_detection_id="llm_001",
        human_detection_id="human_001",
        file_path="src/main.py",
        line_start=10,
        line_end=15,
        jaccard_index=0.85,
        cosine_similarity=0.92,
        is_match=True,
        match_reason="Exact line overlap with high description similarity"
    )
    
    assert alignment.llm_detection_id == "llm_001"
    assert alignment.human_detection_id == "human_001"
    assert alignment.file_path == "src/main.py"
    assert alignment.line_start == 10
    assert alignment.line_end == 15
    assert alignment.jaccard_index == 0.85
    assert alignment.cosine_similarity == 0.92
    assert alignment.is_match is True
    assert alignment.match_reason == "Exact line overlap with high description similarity"
    
    alignment_dict = alignment.to_dict()
    alignment_restored = AlignmentResult.from_dict(alignment_dict)
    
    assert alignment_restored.llm_detection_id == alignment.llm_detection_id
    assert alignment_restored.human_detection_id == alignment.human_detection_id
    assert alignment_restored.is_match == alignment.is_match


def test_severity_invalid():
    """Test invalid severity handling."""
    with pytest.raises(ValueError):
        Severity.from_string("nonexistent")
    
    with pytest.raises(ValueError):
        Severity.from_string("")