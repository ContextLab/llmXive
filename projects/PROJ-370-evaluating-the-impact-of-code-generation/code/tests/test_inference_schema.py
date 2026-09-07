import pytest
import json
from code.src.inference.schema import InferenceRequest, InferenceResponse, InferenceStatus
from code.src.detection.schema import LLMCodeDetectionResult, ConfidenceLevel


class TestInferenceRequest:
    def test_create_request(self):
        """Test basic creation of an InferenceRequest."""
        req = InferenceRequest(
            pr_id="PR-123",
            repo_name="microsoft/vscode",
            diff_text="+ print('hello')",
            file_path="src/main.py",
            line_start=10,
            line_end=11
        )
        assert req.pr_id == "PR-123"
        assert req.diff_text == "+ print('hello')"
        assert req.line_start == 10

    def test_request_to_dict(self):
        """Test serialization of InferenceRequest to dict."""
        req = InferenceRequest(
            pr_id="PR-456",
            repo_name="owner/repo",
            diff_text="- old\n+ new",
            file_path="utils/helper.py",
            line_start=5,
            line_end=6,
            context_window="def helper():\n",
            request_metadata={"source": "github_api"}
        )
        data = req.to_dict()
        
        assert data["pr_id"] == "PR-456"
        assert data["file_path"] == "utils/helper.py"
        assert data["context_window"] == "def helper():\n"
        assert data["request_metadata"]["source"] == "github_api"

    def test_request_json_roundtrip(self):
        """Test JSON serialization and deserialization of InferenceRequest."""
        req = InferenceRequest(
            pr_id="PR-789",
            repo_name="test/test",
            diff_text="bug fix",
            file_path="fix.py",
            line_start=1,
            line_end=2
        )
        
        json_str = req.to_json()
        loaded = InferenceRequest.from_dict(json.loads(json_str))
        
        assert loaded.pr_id == req.pr_id
        assert loaded.diff_text == req.diff_text
        assert loaded.file_path == req.file_path

    def test_request_with_llm_detection(self):
        """Test InferenceRequest containing an LLMCodeDetectionResult."""
        llm_det = LLMCodeDetectionResult(
            pr_id="PR-999",
            file_path="code.py",
            line_start=1,
            line_end=5,
            confidence=ConfidenceLevel.HIGH,
            is_llm_generated=True
        )
        
        req = InferenceRequest(
            pr_id="PR-999",
            repo_name="test/repo",
            diff_text="generated code",
            file_path="code.py",
            line_start=1,
            line_end=5,
            llm_detection_result=llm_det
        )
        
        data = req.to_dict()
        assert data["llm_detection_result"] is not None
        assert data["llm_detection_result"]["confidence"] == "high"
        
        loaded = InferenceRequest.from_dict(data)
        assert loaded.llm_detection_result is not None
        assert loaded.llm_detection_result.is_llm_generated is True


class TestInferenceResponse:
    def test_create_response(self):
        """Test basic creation of an InferenceResponse."""
        resp = InferenceResponse(
            request_id="REQ-001",
            status=InferenceStatus.COMPLETED
        )
        assert resp.request_id == "REQ-001"
        assert resp.status == InferenceStatus.COMPLETED
        assert resp.detected_bugs == []

    def test_response_with_bugs(self):
        """Test response containing detected bugs."""
        bugs = [
            {
                "file_path": "main.py",
                "line_start": 10,
                "line_end": 12,
                "severity": "major",
                "description": "Potential null pointer exception"
            }
        ]
        resp = InferenceResponse(
            request_id="REQ-002",
            status=InferenceStatus.COMPLETED,
            detected_bugs=bugs,
            model_id="starcoder2-3b",
            latency_seconds=12.5
        )
        
        assert len(resp.detected_bugs) == 1
        assert resp.latency_seconds == 12.5

    def test_response_to_dict(self):
        """Test serialization of InferenceResponse to dict."""
        resp = InferenceResponse(
            request_id="REQ-003",
            status=InferenceStatus.FAILED,
            error_message="Model timeout",
            metadata={"retry_count": 3}
        )
        data = resp.to_dict()
        
        assert data["status"] == "failed"
        assert data["error_message"] == "Model timeout"
        assert data["metadata"]["retry_count"] == 3

    def test_response_json_roundtrip(self):
        """Test JSON serialization and deserialization of InferenceResponse."""
        bugs = [
            {"file_path": "a.py", "line_start": 1, "line_end": 1, "severity": "minor", "description": "Style"}
        ]
        resp = InferenceResponse(
            request_id="REQ-004",
            status=InferenceStatus.COMPLETED,
            detected_bugs=bugs,
            raw_output="Found 1 bug: Style issue in a.py"
        )
        
        json_str = resp.to_json()
        loaded = InferenceResponse.from_dict(json.loads(json_str))
        
        assert loaded.request_id == resp.request_id
        assert loaded.status == resp.status
        assert len(loaded.detected_bugs) == 1
        assert loaded.raw_output == resp.raw_output

    def test_response_timeout_status(self):
        """Test response with TIMEOUT status."""
        resp = InferenceResponse(
            request_id="REQ-005",
            status=InferenceStatus.TIMEOUT,
            error_message="Execution exceeded 60s limit"
        )
        assert resp.status == InferenceStatus.TIMEOUT