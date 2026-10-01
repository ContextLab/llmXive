import pytest
import json
from code.src.inference.schema import InferenceRequest, InferenceResponse, InferenceStatus
from code.src.detection.schema import LLMCodeDetectionResult, ConfidenceLevel
from code.src.extraction.schema import Severity


class TestInferenceRequest:
    def test_create_request(self):
        """Test basic creation of an InferenceRequest."""
        req = InferenceRequest(
            pr_id="PR-123",
            repo_name="test/repo",
            diff_text="+ new line\n- old line",
            file_path="src/main.py",
            line_start=10,
            line_end=15
        )
        assert req.pr_id == "PR-123"
        assert req.repo_name == "test/repo"
        assert req.file_path == "src/main.py"
        assert req.line_start == 10
        assert req.line_end == 15
        assert req.severity_hint is None
        assert req.llm_detection_result is None

    def test_create_request_with_optional_fields(self):
        """Test creation with optional fields populated."""
        severity = Severity.MAJOR
        llm_res = LLMCodeDetectionResult(
            is_llm_generated=True,
            confidence=ConfidenceLevel.HIGH,
            details={"reason": "pattern_match"}
        )

        req = InferenceRequest(
            pr_id="PR-456",
            repo_name="test/repo",
            diff_text="diff content",
            file_path="test.py",
            line_start=1,
            line_end=10,
            severity_hint=severity,
            llm_detection_result=llm_res,
            context_window_size=2048,
            metadata={"source": "manual"}
        )

        assert req.severity_hint == severity
        assert req.llm_detection_result is not None
        assert req.llm_detection_result.is_llm_generated is True
        assert req.context_window_size == 2048
        assert req.metadata["source"] == "manual"

    def test_to_dict_and_json(self):
        """Test serialization methods."""
        req = InferenceRequest(
            pr_id="PR-789",
            repo_name="test/repo",
            diff_text="diff",
            file_path="a.py",
            line_start=1,
            line_end=2,
            severity_hint=Severity.MINOR
        )

        data = req.to_dict()
        assert data["pr_id"] == "PR-789"
        assert data["severity_hint"] == "minor"

        json_str = req.to_json()
        assert isinstance(json_str, str)
        assert "PR-789" in json_str

    def test_from_dict_roundtrip(self):
        """Test deserialization from dictionary."""
        original = InferenceRequest(
            pr_id="PR-999",
            repo_name="org/proj",
            diff_text="diff text",
            file_path="file.py",
            line_start=5,
            line_end=10,
            severity_hint=Severity.CRITICAL,
            metadata={"key": "val"}
        )

        data = original.to_dict()
        reconstructed = InferenceRequest.from_dict(data)

        assert reconstructed.pr_id == original.pr_id
        assert reconstructed.repo_name == original.repo_name
        assert reconstructed.file_path == original.file_path
        assert reconstructed.line_start == original.line_start
        assert reconstructed.line_end == original.line_end
        assert reconstructed.severity_hint == original.severity_hint
        assert reconstructed.metadata == original.metadata

    def test_from_dict_with_llm_result(self):
        """Test deserialization when llm_detection_result is present."""
        llm_data = {
            "is_llm_generated": True,
            "confidence": "high",
            "details": {"reason": "test"}
        }
        data = {
            "pr_id": "PR-111",
            "repo_name": "x/y",
            "diff_text": "d",
            "file_path": "f.py",
            "line_start": 1,
            "line_end": 2,
            "llm_detection_result": llm_data
        }

        req = InferenceRequest.from_dict(data)
        assert req.llm_detection_result is not None
        assert req.llm_detection_result.is_llm_generated is True


class TestInferenceResponse:
    def test_create_response(self):
        """Test basic creation of an InferenceResponse."""
        res = InferenceResponse(
            request_id="PR-123",
            status=InferenceStatus.COMPLETED
        )
        assert res.request_id == "PR-123"
        assert res.status == InferenceStatus.COMPLETED
        assert res.detected_bugs == []
        assert res.is_successful() is True

    def test_create_response_with_bugs(self):
        """Test creation with detected bugs."""
        bugs = [
            {"file": "a.py", "line": 10, "severity": "major", "desc": "bug 1"},
            {"file": "b.py", "line": 20, "severity": "minor", "desc": "bug 2"}
        ]
        res = InferenceResponse(
            request_id="PR-123",
            status=InferenceStatus.COMPLETED,
            detected_bugs=bugs,
            raw_output="Found 2 bugs...",
            latency_seconds=1.5,
            model_id="starcoder2-3b"
        )

        assert res.has_detected_bugs() is True
        assert len(res.detected_bugs) == 2
        assert res.latency_seconds == 1.5
        assert res.model_id == "starcoder2-3b"

    def test_create_response_with_error(self):
        """Test creation when inference fails or parsing errors occur."""
        res = InferenceResponse(
            request_id="PR-456",
            status=InferenceStatus.FAILED,
            parsing_error="JSON parse error: unexpected token"
        )
        assert res.status == InferenceStatus.FAILED
        assert res.parsing_error is not None
        assert res.is_successful() is False

    def test_create_response_timeout(self):
        """Test creation with timeout status."""
        res = InferenceResponse(
            request_id="PR-789",
            status=InferenceStatus.TIMEOUT,
            latency_seconds=300.0
        )
        assert res.status == InferenceStatus.TIMEOUT
        assert res.is_successful() is False

    def test_to_dict_and_json(self):
        """Test serialization methods."""
        res = InferenceResponse(
            request_id="PR-999",
            status=InferenceStatus.COMPLETED,
            detected_bugs=[{"line": 5}],
            model_id="model-v1"
        )

        data = res.to_dict()
        assert data["request_id"] == "PR-999"
        assert data["status"] == "completed"
        assert len(data["detected_bugs"]) == 1

        json_str = res.to_json()
        assert "PR-999" in json_str

    def test_from_dict_roundtrip(self):
        """Test deserialization from dictionary."""
        original = InferenceResponse(
            request_id="PR-888",
            status=InferenceStatus.COMPLETED,
            detected_bugs=[{"line": 10, "severity": "critical"}],
            raw_output="output",
            latency_seconds=2.0,
            model_id="test-model"
        )

        data = original.to_dict()
        reconstructed = InferenceResponse.from_dict(data)

        assert reconstructed.request_id == original.request_id
        assert reconstructed.status == original.status
        assert reconstructed.detected_bugs == original.detected_bugs
        assert reconstructed.latency_seconds == original.latency_seconds
        assert reconstructed.model_id == original.model_id

    def test_from_dict_invalid_status(self):
        """Test deserialization with invalid status string."""
        data = {
            "request_id": "PR-000",
            "status": "invalid_status_string",
            "detected_bugs": []
        }
        res = InferenceResponse.from_dict(data)
        # Should fallback to FAILED or default based on implementation
        assert res.request_id == "PR-000"
        # The implementation defaults to FAILED on ValueError
        assert res.status == InferenceStatus.FAILED