import pytest
from code.src.extraction.schema import (
    Severity,
    PullRequest,
    BugDetection,
    AlignmentResult,
)


class TestSeverity:
    def test_severity_from_string_valid(self):
        assert Severity.from_string("critical") == Severity.CRITICAL
        assert Severity.from_string("CRITICAL") == Severity.CRITICAL
        assert Severity.from_string("major") == Severity.MAJOR
        assert Severity.from_string("minor") == Severity.MINOR
        assert Severity.from_string("style") == Severity.STYLE

    def test_severity_from_string_invalid(self):
        with pytest.raises(ValueError):
            Severity.from_string("invalid_severity")

    def test_severity_value(self):
        assert Severity.CRITICAL.value == "critical"
        assert Severity.MAJOR.value == "major"
        assert Severity.MINOR.value == "minor"
        assert Severity.STYLE.value == "style"


class TestPullRequest:
    @pytest.fixture
    def sample_pr_data(self):
        return {
            "pr_id": "PR-123",
            "repo_name": "test/repo",
            "title": "Test PR",
            "body": "Test body",
            "state": "open",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
            "author": "testuser",
            "base_branch": "main",
            "head_branch": "feature",
            "diff": "+ new code\n- old code",
            "files_changed": [{"path": "test.py", "additions": 1, "deletions": 1}],
            "linked_issue_ids": [42],
            "review_comments": [{"text": "LGTM", "author": "reviewer"}],
            "is_llm_generated": False,
            "checksum": "abc123",
        }

    def test_pull_request_creation(self, sample_pr_data):
        pr = PullRequest.from_dict(sample_pr_data)
        assert pr.pr_id == "PR-123"
        assert pr.repo_name == "test/repo"
        assert pr.is_llm_generated is False
        assert pr.checksum == "abc123"

    def test_pull_request_json_roundtrip(self, sample_pr_data):
        pr = PullRequest.from_dict(sample_pr_data)
        json_str = pr.to_json()
        pr_restored = PullRequest.from_json(json_str)
        assert pr_restored.pr_id == pr.pr_id
        assert pr_restored.diff == pr.diff
        assert pr_restored.linked_issue_ids == pr.linked_issue_ids

    def test_pull_request_to_dict(self, sample_pr_data):
        pr = PullRequest.from_dict(sample_pr_data)
        result = pr.to_dict()
        assert result["pr_id"] == "PR-123"
        assert result["diff"] == "+ new code\n- old code"

    def test_pull_request_optional_fields(self):
        pr = PullRequest(
            pr_id="PR-456",
            repo_name="test/repo",
            title="Test",
            body=None,
            state="open",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            author="user",
            base_branch="main",
            head_branch="feat",
            diff="",
            files_changed=[],
            linked_issue_ids=[],
            review_comments=[],
        )
        assert pr.body is None
        assert pr.is_llm_generated is None
        assert pr.checksum is None


class TestBugDetection:
    @pytest.fixture
    def sample_bug_data(self):
        return {
            "pr_id": "PR-123",
            "file_path": "src/main.py",
            "line_start": 10,
            "line_end": 15,
            "severity": "critical",
            "description": "Null pointer exception",
            "source": "human",
            "confidence": 0.95,
            "is_verified": True,
            "verification_method": "strict_triangulation",
        }

    def test_bug_detection_creation(self, sample_bug_data):
        bug = BugDetection.from_dict(sample_bug_data)
        assert bug.pr_id == "PR-123"
        assert bug.severity == Severity.CRITICAL
        assert bug.is_verified is True

    def test_bug_detection_severity(self, sample_bug_data):
        bug = BugDetection.from_dict(sample_bug_data)
        assert bug.severity == Severity.CRITICAL

        sample_bug_data["severity"] = "major"
        bug = BugDetection.from_dict(sample_bug_data)
        assert bug.severity == Severity.MAJOR

    def test_bug_detection_json_roundtrip(self, sample_bug_data):
        bug = BugDetection.from_dict(sample_bug_data)
        json_str = bug.to_json()
        bug_restored = BugDetection.from_json(json_str)
        assert bug_restored.pr_id == bug.pr_id
        assert bug_restored.severity == bug.severity
        assert bug_restored.is_verified == bug.is_verified

    def test_bug_detection_optional_fields(self):
        bug = BugDetection(
            pr_id="PR-789",
            file_path="test.py",
            line_start=1,
            line_end=5,
            severity=Severity.MINOR,
            description="Minor issue",
            source="llm",
        )
        assert bug.confidence is None
        assert bug.is_verified is False
        assert bug.verification_method is None


class TestAlignmentResult:
    @pytest.fixture
    def sample_alignment_data(self, sample_bug_data):
        human_bug = BugDetection.from_dict(sample_bug_data)
        llm_bug = BugDetection.from_dict({
            **sample_bug_data,
            "source": "llm",
            "is_verified": False,
            "verification_method": None,
        })
        return {
            "human_bug": human_bug.to_dict(),
            "llm_bug": llm_bug.to_dict(),
            "match_score": 0.92,
            "jaccard_index": 0.85,
            "cosine_similarity": 0.90,
            "is_valid_match": True,
            "match_reason": "High overlap and similarity",
        }

    def test_alignment_result_creation(self, sample_alignment_data):
        result = AlignmentResult.from_dict(sample_alignment_data)
        assert result.match_score == 0.92
        assert result.is_valid_match is True
        assert result.human_bug.source == "human"
        assert result.llm_bug.source == "llm"

    def test_alignment_result_json_roundtrip(self, sample_alignment_data):
        result = AlignmentResult.from_dict(sample_alignment_data)
        json_str = result.to_json()
        result_restored = AlignmentResult.from_json(json_str)
        assert result_restored.match_score == result.match_score
        assert result_restored.jaccard_index == result.jaccard_index
        assert result_restored.human_bug.pr_id == result.human_bug.pr_id

    def test_alignment_result_fields(self, sample_alignment_data):
        result = AlignmentResult.from_dict(sample_alignment_data)
        assert result.match_score == 0.92
        assert result.jaccard_index == 0.85
        assert result.cosine_similarity == 0.90
        assert result.is_valid_match is True
        assert result.match_reason == "High overlap and similarity"
