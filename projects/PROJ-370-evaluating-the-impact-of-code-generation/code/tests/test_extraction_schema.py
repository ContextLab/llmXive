"""
Unit tests for the extraction module schema.

Tests for Severity, PullRequest, BugDetection, and AlignmentResult classes.
"""
import pytest
import json
from code.src.extraction.schema import Severity, PullRequest, BugDetection, AlignmentResult


class TestSeverity:
    """Tests for the Severity enum."""

    def test_severity_values(self):
        """Test that all severity values are correctly defined."""
        assert Severity.CRITICAL.value == "critical"
        assert Severity.MAJOR.value == "major"
        assert Severity.MINOR.value == "minor"
        assert Severity.STYLE.value == "style"
        assert Severity.INFO.value == "info"

    def test_from_string_valid(self):
        """Test conversion from valid string to Severity."""
        assert Severity.from_string("critical") == Severity.CRITICAL
        assert Severity.from_string("CRITICAL") == Severity.CRITICAL
        assert Severity.from_string("Major") == Severity.MAJOR
        assert Severity.from_string("minor") == Severity.MINOR

    def test_from_string_invalid(self):
        """Test that invalid severity strings raise ValueError."""
        with pytest.raises(ValueError):
            Severity.from_string("invalid_severity")

    def test_str_representation(self):
        """Test string representation of Severity."""
        assert str(Severity.CRITICAL) == "critical"
        assert str(Severity.MAJOR) == "major"


class TestPullRequest:
    """Tests for the PullRequest dataclass."""

    def test_pull_request_creation(self):
        """Test creating a PullRequest instance."""
        pr = PullRequest(
            pr_id="123",
            repo_name="test/repo",
            title="Test PR",
            body="Test body",
            state="open",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            merged_at=None,
            author="testuser",
            diff="diff content",
        )
        assert pr.pr_id == "123"
        assert pr.repo_name == "test/repo"
        assert pr.title == "Test PR"
        assert pr.llm_code_flag is False
        assert pr.truncation_flag is False

    def test_pull_request_default_values(self):
        """Test that default values are set correctly."""
        pr = PullRequest(
            pr_id="456",
            repo_name="test/repo",
            title="Another PR",
            body=None,
            state="closed",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            merged_at=None,
            author="anotheruser",
            diff="another diff",
        )
        assert pr.linked_issue_ids == []
        assert pr.comments == []

    def test_pull_request_to_dict(self):
        """Test conversion to dictionary."""
        pr = PullRequest(
            pr_id="789",
            repo_name="test/repo",
            title="Dict Test",
            body="Body",
            state="merged",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            merged_at="2023-01-02T00:00:00Z",
            author="user",
            diff="diff",
            linked_issue_ids=[1, 2],
        )
        pr_dict = pr.to_dict()
        assert pr_dict["pr_id"] == "789"
        assert pr_dict["linked_issue_ids"] == [1, 2]
        assert pr_dict["merged_at"] == "2023-01-02T00:00:00Z"

    def test_pull_request_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "pr_id": "111",
            "repo_name": "test/repo",
            "title": "From Dict",
            "body": "Body",
            "state": "open",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "merged_at": None,
            "author": "user",
            "diff": "diff",
            "linked_issue_ids": [3, 4],
            "comments": [],
            "llm_code_flag": True,
            "truncation_flag": False,
        }
        pr = PullRequest.from_dict(data)
        assert pr.pr_id == "111"
        assert pr.linked_issue_ids == [3, 4]
        assert pr.llm_code_flag is True

    def test_pull_request_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        pr = PullRequest(
            pr_id="222",
            repo_name="test/repo",
            title="JSON Test",
            body="Body",
            state="open",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            merged_at=None,
            author="user",
            diff="diff",
        )
        json_str = pr.to_json()
        pr_restored = PullRequest.from_json(json_str)
        assert pr_restored.pr_id == pr.pr_id
        assert pr_restored.title == pr.title


class TestBugDetection:
    """Tests for the BugDetection dataclass."""

    def test_bug_detection_creation(self):
        """Test creating a BugDetection instance."""
        bug = BugDetection(
            pr_id="123",
            file_path="src/main.py",
            line_start=10,
            line_end=15,
            severity=Severity.CRITICAL,
            description="Null pointer exception",
            detection_method="llm",
            confidence=0.95,
        )
        assert bug.pr_id == "123"
        assert bug.severity == Severity.CRITICAL
        assert bug.confidence == 0.95

    def test_bug_detection_to_dict(self):
        """Test conversion to dictionary."""
        bug = BugDetection(
            pr_id="123",
            file_path="src/main.py",
            line_start=10,
            line_end=15,
            severity=Severity.MAJOR,
            description="Test bug",
            detection_method="heuristic",
            confidence=0.8,
            is_confirmed=True,
        )
        bug_dict = bug.to_dict()
        assert bug_dict["severity"] == "major"
        assert bug_dict["is_confirmed"] is True

    def test_bug_detection_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "pr_id": "456",
            "file_path": "src/utils.py",
            "line_start": 20,
            "line_end": 25,
            "severity": "minor",
            "description": "Style issue",
            "detection_method": "human",
            "confidence": 1.0,
            "is_confirmed": True,
        }
        bug = BugDetection.from_dict(data)
        assert bug.pr_id == "456"
        assert bug.severity == Severity.MINOR
        assert bug.detection_method == "human"

    def test_bug_detection_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        bug = BugDetection(
            pr_id="789",
            file_path="src/test.py",
            line_start=5,
            line_end=10,
            severity=Severity.STYLE,
            description="Formatting issue",
            detection_method="llm",
            confidence=0.5,
        )
        json_str = bug.to_json()
        bug_restored = BugDetection.from_json(json_str)
        assert bug_restored.pr_id == bug.pr_id
        assert bug_restored.severity == bug.severity


class TestAlignmentResult:
    """Tests for the AlignmentResult dataclass."""

    def test_alignment_result_creation(self):
        """Test creating an AlignmentResult instance."""
        alignment = AlignmentResult(
            pr_id="123",
            llm_bug_id="bug_1",
            human_bug_id="human_bug_1",
            file_path="src/main.py",
            line_start_llm=10,
            line_end_llm=15,
            line_start_human=11,
            line_end_human=16,
            jaccard_index=0.8,
            similarity_score=0.9,
            is_aligned=True,
            alignment_method="jaccard",
        )
        assert alignment.pr_id == "123"
        assert alignment.is_aligned is True
        assert alignment.human_bug_id == "human_bug_1"

    def test_alignment_result_unmatched(self):
        """Test alignment result with no human match."""
        alignment = AlignmentResult(
            pr_id="123",
            llm_bug_id="bug_2",
            human_bug_id=None,
            file_path="src/main.py",
            line_start_llm=20,
            line_end_llm=25,
            line_start_human=None,
            line_end_human=None,
            jaccard_index=0.0,
            similarity_score=0.1,
            is_aligned=False,
            alignment_method="jaccard",
        )
        assert alignment.human_bug_id is None
        assert alignment.is_aligned is False

    def test_alignment_result_to_dict(self):
        """Test conversion to dictionary."""
        alignment = AlignmentResult(
            pr_id="456",
            llm_bug_id="bug_3",
            human_bug_id="human_bug_2",
            file_path="src/utils.py",
            line_start_llm=30,
            line_end_llm=35,
            line_start_human=30,
            line_end_human=35,
            jaccard_index=1.0,
            similarity_score=1.0,
            is_aligned=True,
            alignment_method="cosine",
        )
        alignment_dict = alignment.to_dict()
        assert alignment_dict["jaccard_index"] == 1.0
        assert alignment_dict["similarity_score"] == 1.0

    def test_alignment_result_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "pr_id": "789",
            "llm_bug_id": "bug_4",
            "human_bug_id": None,
            "file_path": "src/test.py",
            "line_start_llm": 40,
            "line_end_llm": 45,
            "line_start_human": None,
            "line_end_human": None,
            "jaccard_index": 0.0,
            "similarity_score": 0.2,
            "is_aligned": False,
            "alignment_method": "jaccard",
        }
        alignment = AlignmentResult.from_dict(data)
        assert alignment.human_bug_id is None
        assert alignment.is_aligned is False

    def test_alignment_result_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        alignment = AlignmentResult(
            pr_id="111",
            llm_bug_id="bug_5",
            human_bug_id="human_bug_3",
            file_path="src/main.py",
            line_start_llm=50,
            line_end_llm=55,
            line_start_human=51,
            line_end_human=56,
            jaccard_index=0.75,
            similarity_score=0.85,
            is_aligned=True,
            alignment_method="jaccard",
        )
        json_str = alignment.to_json()
        alignment_restored = AlignmentResult.from_json(json_str)
        assert alignment_restored.pr_id == alignment.pr_id
        assert alignment_restored.jaccard_index == alignment.jaccard_index