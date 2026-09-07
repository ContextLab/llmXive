"""
Unit tests for extraction schema dataclasses.
Tests PullRequest, BugDetection, AlignmentResult, and Severity.
"""
import pytest
from code.src.extraction.schema import (
    Severity,
    PullRequest,
    BugDetection,
    AlignmentResult
)


class TestSeverity:
    """Tests for Severity enum."""

    def test_severity_from_string_valid(self):
        """Test converting valid strings to Severity."""
        assert Severity.from_string("critical") == Severity.CRITICAL
        assert Severity.from_string("major") == Severity.MAJOR
        assert Severity.from_string("minor") == Severity.MINOR
        assert Severity.from_string("style") == Severity.STYLE
        # Case insensitive
        assert Severity.from_string("CRITICAL") == Severity.CRITICAL

    def test_severity_from_string_invalid(self):
        """Test that invalid strings raise ValueError."""
        with pytest.raises(ValueError):
            Severity.from_string("invalid_severity")

    def test_severity_values(self):
        """Test Severity enum values."""
        assert Severity.CRITICAL.value == "critical"
        assert Severity.MAJOR.value == "major"
        assert Severity.MINOR.value == "minor"
        assert Severity.STYLE.value == "style"


class TestPullRequest:
    """Tests for PullRequest dataclass."""

    def test_pull_request_creation(self):
        """Test basic PullRequest creation."""
        pr = PullRequest(
            pr_id=123,
            repo_name="test/repo",
            title="Test PR",
            body="Test body",
            state="open",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            user_login="testuser",
            diff_url="https://github.com/test/repo/pull/123.diff",
            html_url="https://github.com/test/repo/pull/123",
            diff_text="+ print('hello')\n- print('world')"
        )

        assert pr.pr_id == 123
        assert pr.repo_name == "test/repo"
        assert pr.title == "Test PR"
        assert pr.state == "open"
        assert len(pr.comments) == 0
        assert len(pr.linked_issue_ids) == 0

    def test_pull_request_with_comments_and_issues(self):
        """Test PullRequest with comments and linked issues."""
        pr = PullRequest(
            pr_id=456,
            repo_name="test/repo",
            title="Another PR",
            body=None,
            state="closed",
            created_at="2024-01-02T00:00:00Z",
            updated_at="2024-01-02T00:00:00Z",
            user_login="anotheruser",
            diff_url="https://github.com/test/repo/pull/456.diff",
            html_url="https://github.com/test/repo/pull/456",
            diff_text="diff content",
            comments=[
                {"id": 1, "body": "Good catch!", "user": "reviewer1"},
                {"id": 2, "body": "LGTM", "user": "reviewer2"}
            ],
            linked_issue_ids=[789, 790]
        )

        assert len(pr.comments) == 2
        assert len(pr.linked_issue_ids) == 2
        assert pr.linked_issue_ids == [789, 790]

    def test_pull_request_to_dict(self):
        """Test PullRequest to_dict conversion."""
        pr = PullRequest(
            pr_id=1,
            repo_name="test/repo",
            title="Test",
            body=None,
            state="open",
            created_at="2024-01-01",
            updated_at="2024-01-01",
            user_login="user",
            diff_url="url",
            html_url="url",
            diff_text="diff",
            is_truncated=True,
            token_count=100,
            checksum="abc123"
        )

        pr_dict = pr.to_dict()

        assert pr_dict["pr_id"] == 1
        assert pr_dict["is_truncated"] is True
        assert pr_dict["token_count"] == 100
        assert pr_dict["checksum"] == "abc123"

    def test_pull_request_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        original = PullRequest(
            pr_id=999,
            repo_name="org/project",
            title="JSON Test",
            body="Body text",
            state="merged",
            created_at="2024-02-01T12:00:00Z",
            updated_at="2024-02-02T12:00:00Z",
            user_login="jsonuser",
            diff_url="https://example.com/diff",
            html_url="https://example.com/pr",
            diff_text="line1\nline2",
            comments=[{"id": 1, "body": "comment"}],
            linked_issue_ids=[100],
            is_truncated=False,
            token_count=50,
            checksum="def456"
        )

        json_str = original.to_json()
        restored = PullRequest.from_dict(eval(json_str))

        assert restored.pr_id == original.pr_id
        assert restored.repo_name == original.repo_name
        assert restored.title == original.title
        assert restored.diff_text == original.diff_text
        assert restored.linked_issue_ids == original.linked_issue_ids
        assert restored.checksum == original.checksum


class TestBugDetection:
    """Tests for BugDetection dataclass."""

    def test_bug_detection_creation(self):
        """Test basic BugDetection creation."""
        bug = BugDetection(
            pr_id=123,
            file_path="src/main.py",
            line_start=10,
            line_end=15,
            severity=Severity.MAJOR,
            description="Potential null pointer",
            detection_source="human"
        )

        assert bug.pr_id == 123
        assert bug.file_path == "src/main.py"
        assert bug.line_start == 10
        assert bug.line_end == 15
        assert bug.severity == Severity.MAJOR
        assert bug.detection_source == "human"
        assert bug.is_verified is False

    def test_bug_detection_with_severity_string(self):
        """Test BugDetection with string severity in from_dict."""
        data = {
            "pr_id": 456,
            "file_path": "test.py",
            "line_start": 5,
            "line_end": 8,
            "severity": "critical",
            "description": "Critical bug",
            "detection_source": "llm",
            "confidence": 0.95,
            "is_verified": True,
            "verification_method": "strict_triangulation"
        }

        bug = BugDetection.from_dict(data)

        assert bug.severity == Severity.CRITICAL
        assert bug.confidence == 0.95
        assert bug.is_verified is True

    def test_bug_detection_to_dict(self):
        """Test BugDetection to_dict conversion."""
        bug = BugDetection(
            pr_id=1,
            file_path="app.py",
            line_start=20,
            line_end=25,
            severity=Severity.MINOR,
            description="Minor issue",
            detection_source="llm",
            confidence=0.8,
            is_verified=False,
            llm_error_flag=False
        )

        bug_dict = bug.to_dict()

        assert bug_dict["severity"] == "minor"
        assert bug_dict["confidence"] == 0.8
        assert bug_dict["llm_error_flag"] is False

    def test_bug_detection_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        original = BugDetection(
            pr_id=777,
            file_path="module/utils.py",
            line_start=100,
            line_end=110,
            severity=Severity.STYLE,
            description="Style violation",
            detection_source="human",
            confidence=1.0,
            is_verified=True,
            verification_method="manual_review",
            raw_context="context here"
        )

        json_str = original.to_json()
        restored = BugDetection.from_dict(eval(json_str))

        assert restored.pr_id == original.pr_id
        assert restored.file_path == original.file_path
        assert restored.severity == original.severity
        assert restored.description == original.description
        assert restored.raw_context == original.raw_context


class TestAlignmentResult:
    """Tests for AlignmentResult dataclass."""

    def test_alignment_result_creation(self):
        """Test basic AlignmentResult creation."""
        human_bug = BugDetection(
            pr_id=1,
            file_path="a.py",
            line_start=1,
            line_end=5,
            severity=Severity.MAJOR,
            description="Human found bug",
            detection_source="human",
            is_verified=True
        )

        llm_bug = BugDetection(
            pr_id=1,
            file_path="a.py",
            line_start=1,
            line_end=5,
            severity=Severity.MAJOR,
            description="LLM found bug",
            detection_source="llm"
        )

        alignment = AlignmentResult(
            human_bug=human_bug,
            llm_bug=llm_bug,
            match_score=0.95,
            jaccard_index=1.0,
            cosine_similarity=0.98,
            is_match=True
        )

        assert alignment.is_match is True
        assert alignment.match_score == 0.95
        assert alignment.jaccard_index == 1.0

    def test_alignment_result_to_dict(self):
        """Test AlignmentResult to_dict conversion."""
        human_bug = BugDetection(
            pr_id=1,
            file_path="test.py",
            line_start=1,
            line_end=3,
            severity=Severity.CRITICAL,
            description="Test",
            detection_source="human"
        )

        llm_bug = BugDetection(
            pr_id=1,
            file_path="test.py",
            line_start=1,
            line_end=3,
            severity=Severity.CRITICAL,
            description="Test",
            detection_source="llm"
        )

        alignment = AlignmentResult(
            human_bug=human_bug,
            llm_bug=llm_bug,
            match_score=0.85,
            jaccard_index=0.8,
            cosine_similarity=0.9,
            is_match=True,
            match_criteria={"threshold": 0.85}
        )

        alignment_dict = alignment.to_dict()

        assert "human_bug" in alignment_dict
        assert "llm_bug" in alignment_dict
        assert alignment_dict["match_score"] == 0.85
        assert alignment_dict["match_criteria"]["threshold"] == 0.85

    def test_alignment_result_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        human_bug = BugDetection(
            pr_id=123,
            file_path="src/core.py",
            line_start=50,
            line_end=60,
            severity=Severity.MAJOR,
            description="Human detection",
            detection_source="human",
            is_verified=True
        )

        llm_bug = BugDetection(
            pr_id=123,
            file_path="src/core.py",
            line_start=50,
            line_end=60,
            severity=Severity.MAJOR,
            description="LLM detection",
            detection_source="llm",
            confidence=0.9
        )

        original = AlignmentResult(
            human_bug=human_bug,
            llm_bug=llm_bug,
            match_score=0.92,
            jaccard_index=0.88,
            cosine_similarity=0.94,
            is_match=True,
            match_criteria={"exact_lines": True}
        )

        json_str = original.to_json()
        restored = AlignmentResult.from_dict(eval(json_str))

        assert restored.human_bug.pr_id == original.human_bug.pr_id
        assert restored.llm_bug.detection_source == "llm"
        assert restored.is_match is True
        assert restored.match_score == 0.92
        assert restored.jaccard_index == 0.88
        assert restored.match_criteria["exact_lines"] is True